import pyqtgraph as pg
import numpy as np
from PyQt5 import QtGui
from pylsl import StreamInlet

###################################################
## Plotting Module
###################################################


## Wrapper Functions ##
###################################################

def plotTimeDomain(stream_info, fs=0, channels=0, timewin=30, tickfactor=5, size=(1500, 800), title=None):
    '''Plot Real-Time in the time domain using a scrolling plot. Wrapper function for plotTimeDomainBackend.

    Accepts a pylsl StreamInlet Object and used backend function to  plot chunks in real-time as they are recieved
    using a scrolling pyqtgraph plot. Can plot multiple channels. Opens backend function in a thread.

    Args:
        stream_info (pylsl StreamInfo Object): The stream info object for the stream to be plotted
        fs (int): The sampling frequency of the device. If zero function will attempt to determine 
            sampling frequency automatically
        channels (list): A list of integers which represent which channels to plot. If set to int zero all channels 
            will be plotted
        timewin (int): The number seconds to show at any given time in the plot. This affects the speed 
            with which the plot will scroll accross the screen. Can not be a prime number.
        tickfactor (int): The number of seconds between x-axis labels. Must be a factor of timewin
        size (array): Array of type (width, height) of the figure
        title (string): Title of the plot figure
    '''

    # Create thread to run plotTimeDomainBackend function without blocking main thread
    thread = threading.Thread(target=plotTimeDomainBackend, 
        kwargs={'stream_info':stream_info, 
            'fs':fs,
            'channels':channels,
            'timewin':timewin,
            'tickfactor':tickfactor,
            'size':size,
            'title':title})
    
    # Start thread
    thread.run()


## Backend Functions ##
###################################################

def plotTimeDomainBackend(stream_info, fs=0, channels=0, timewin=30, tickfactor=5, size=(1500, 800), title=None):
    """Plot Real-Time in the time domain using a scrolling plot.

    Accepts a pylsl StreamInlet Object and plots chunks in real-time as they are recieved
    using a scrolling pyqtgraph plot. Can plot multiple channels.

    Args:
        stream_info (pylsl StreamInfo Object): The stream info object for the stream to be plotted
        fs (int): The sampling frequency of the device. If zero function will attempt to determine 
            sampling frequency automatically
        channels (list): A list of integers which represent which channels to plot. If set to int zero all channels 
            will be plotted
        timewin (int): The number seconds to show at any given time in the plot. This affects the speed 
            with which the plot will scroll accross the screen. Can not be a prime number.
        tickfactor (int): The number of seconds between x-axis labels. Must be a factor of timewin
        size (array): Array of type (width, height) of the figure
        title (string): Title of the plot figure
    """
    #################################
    ## Stream Inlet Creation
    #################################
    inlet = StreamInlet(stream_info, recover=True)
    inlet.open_stream() # Stream is opened implicitely on first call of pull chunk, but opening now for clarity

    #################################
    ## Variable Initialization
    #################################

    ## Get/Check Default Params
    if(timewin%tickfactor != 0):
        print('''ERROR: The tickfactor should be a factor of of timewin. The default tickfactor
        \n is 5 seconds. If you changed the default timewin, make sure that 5 is a factor, or 
        \n change the tickfactor so that it is a factor of timewin''')
        return

    if(fs == 0):
        fs = stream_info.nominal_srate() # Get sampling rate

    # Get list of channels to be plotted
    if(channels == 0):
        numchan = stream_info.channel_count() # number of available channels
        channels = np.linspace(0, numchan-1, numchan)
    else:
        channels = [x-1 for x in channels] # Must shift channel numbers such that they represent indices
    
    for channel in channels:
        if (channel < 0) or (channel > (stream_info.channel_count() - 1)):
            print('''ERROR: Channel Number out of range''')
            return

    ## Initialize Constants
    XWIN = timewin*fs # Width of X-Axis in samples
    XTICKS = (int)((timewin + 1)/tickfactor) # Number of labels to have on X-Axis

    ##################################
    ## Figure and Plot Set Up
    ##################################

    ## Initialize QT
    app = QtGui.QApplication([])

    ## Define a top-level widget to hold everything
    fig = QtGui.QWidget()
    fig.resize(size[0], size[1]) # Resize window
    if (title != None): 
        fig.setWindowTitle(title) # Set window title
    layout = QtGui.QGridLayout()
    fig.setLayout(layout)

    # Set up initial plot conditions
    (x_vec, step) = np.linspace(0,timewin,XWIN+1, retstep=True) # vector used to plot y values
    xlabels = np.zeros(XTICKS).tolist() # Vector to hold labels of ticks on x-axis
    xticks = [ x * tickfactor for x in list(range(0, XTICKS))] # Initialize locations of x-labels
    y_vec = np.zeros((np.size(channels),len(x_vec))) # Initialize y_values as zero

    # Set Up subplots and lines
    plots = []
    curves = []
    colors = ['c', 'm', 'g', 'r', 'y', 'b'] # Color options for various channels
    for i in range(0, np.size(channels)):
        # Create axis item and set tick locations and labels
        axis = pg.AxisItem(orientation='bottom')
        axis.setTicks([[(xticks[i],str(xlabels[i])) for i in range(len(xticks))]]) # Initialize all labels as zero
        # Create plot widget and append to list
        plot = pg.PlotWidget(axisItems={'bottom': axis}, labels={'left': 'Volts (mV)'}, title='Channel ' + (str)(channels[i] + 1)) # Create Plot Widget
        plot.plotItem.setMouseEnabled(x=False, y=False) # Disable panning for widget
        plot.plotItem.showGrid(x=True) # Enable vertical gridlines
        plots.append(plot)
        # Plot data and save curve. Append curve to list
        curve = plot.plot(x_vec, y_vec[i], pen=pg.mkPen(colors[i%len(colors)], width=0.5)) # Set thickness and color of lines
        curves.append(curve)
        # Add plot to main widget
        layout.addWidget(plot, i, 0)

    # Display figure as a new window
    fig.show()

    ###################################
    # Real-Time Plotting Loop
    ###################################

    firstUpdate = True
    while(True):
        chunk = inlet.pull_chunk()

        if chunk: # Check for available chunk
            chunkdata = np.transpose(chunk[0]) # Get chunk data and transpose to be CHANNELS x CHUNKLENGTH
            chunkperiod = len(chunkdata[0])*(1/fs)
            xticks = [x - chunkperiod for x in xticks] # Update location of x-labels

            # Update x-axis locations and labels
            if(xticks[0] < 0): # Check if a label has crossed to the negative side of the y-axis

                # Delete label on left of x-axis and add a new one on the right side
                xticks.pop(0)
                xticks.append(xticks[-1] + tickfactor)

                # Adjust time labels accordingly
                if (firstUpdate == False): # Check to see if it's the first update, if so skip so that time starts at zero
                    xlabels.append(xlabels[-1] + tickfactor)
                    xlabels.pop(0)
                else:
                    firstUpdate = False
            
            # Update plotted data
            for i in range(0,np.size(channels)):
                y_vec[i] = np.append(y_vec[i], chunkdata[int(channels[i])], axis=0)[len(chunkdata[int(channels[i])]):] # Append chunk to the end of y_data
                curves[i].setData(x_vec, y_vec[i]) # Update data

                # Update x-axis labels
                axis = plots[i].getAxis(name='bottom')
                axis.setTicks([[(xticks[i],str(xlabels[i])) for i in range(len(xticks))]])
               
        # Update QT Widget to reflect the changes we made
        pg.QtGui.QApplication.processEvents()

        # Check to see if widget if has been closed, if so exit loop
        if not fig.isVisible():
            break
    
    # Close the stream inlet
    inlet.close_stream()
    
    return

