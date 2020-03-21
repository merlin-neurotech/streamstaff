import os

import numpy as np
import pandas as pd
import pyqtgraph as pg
from pylsl import StreamInlet
from PyQt5 import QtGui

###################################################
# Plotting Module
###################################################


def plotTimeDomain(
    stream_info,
    fs=None,
    channels=None,
    timewin=30,
    tickfactor=5,
    size=(1500, 800),
    title=None,
    save=False,
    savefile="data.csv",
):
    """Plot Real-Time in the time domain using a scrolling plot.

    Accepts a pylsl StreamInlet Object and plots chunks in real-time as they are recieved
    using a scrolling pyqtgraph plot. Can plot multiple channels.

    Args:
        stream_info (pylsl StreamInfo Object): The stream info object for the stream to be plotted
        fs (int): The sampling frequency of the device. If default (None), function will attempt to determine
            sampling frequency automatically
        channels (list): A list of integers which represent which channels to plot. Default (None),
            will plot all available channels
        timewin (int): The number seconds to show at any given time in the plot. This affects the speed
            with which the plot will scroll accross the screen. Can not be a prime number.
        tickfactor (int): The number of seconds between x-axis labels. Must be a factor of timewin.
        size (array): Array of type (width, height) of the figure
        title (string): Title of the plot figure
        save (bool): Whether or not the stream data should also be saved to a file.
        savefile (string): Which file to save the data in. The .csv extension will be automatically added if not present.
    """
    #################################
    # Stream Inlet Creation
    #################################
    inlet = StreamInlet(stream_info, recover=True)
    inlet.open_stream()  # Stream is opened implicitely on first call of pull chunk, but opening now for clarity

    #################################
    # Variable Initialization
    #################################

    # Get/Check Default Params
    if timewin % tickfactor != 0:
        print(
            """ERROR: The tickfactor should be a factor of of timewin. The default tickfactor
        \n is 5 seconds. If you changed the default timewin, make sure that 5 is a factor, or
        \n change the tickfactor so that it is a factor of timewin"""
        )
        return

    if fs is None:
        fs = stream_info.nominal_srate()  # Get sampling rate

    # Get list of channels to be plotted
    if channels is None:
        numchan = stream_info.channel_count()  # number of available channels
        channels = np.linspace(0, numchan - 1, numchan)
    else:
        channels = [
            x - 1 for x in channels
        ]  # Must shift channel numbers such that they represent indices

    for channel in channels:
        if (channel < 0) or (
            channel > (stream_info.channel_count() - 1)
        ):  # Must shift by one since channels holds indices
            print("""ERROR: Channel Number out of range""")
            return

    # Initialize Constants
    XWIN = timewin * fs  # Width of X-Axis in samples
    XTICKS = (int)((timewin + 1) / tickfactor)  # Number of labels to have on X-Axis

    ##################################
    # Figure and Plot Set Up
    ##################################

    # Initialize QT
    app = QtGui.QApplication([])

    # Define a top-level widget to hold everything
    fig = QtGui.QWidget()
    fig.resize(size[0], size[1])  # Resize window
    if title is not None:
        fig.setWindowTitle(title)  # Set window title
    layout = QtGui.QGridLayout()
    fig.setLayout(layout)

    # Set up initial plot conditions
    (x_vec, step) = np.linspace(
        0, timewin, XWIN + 1, retstep=True
    )  # vector used to plot y values
    xlabels = np.zeros(XTICKS).tolist()  # Vector to hold labels of ticks on x-axis
    xticks = [
        x * tickfactor for x in list(range(0, XTICKS))
    ]  # Initialize locations of x-labels
    y_vec = np.zeros((np.size(channels), len(x_vec)))  # Initialize y_values as zero

    # Set Up subplots and lines
    plots = []
    curves = []
    colors = ["c", "m", "g", "r", "y", "b"]  # Color options for various channels
    for i in range(0, np.size(channels)):
        # Create axis item and set tick locations and labels
        axis = pg.AxisItem(orientation="bottom")
        axis.setTicks(
            [[(xticks[i], str(xlabels[i])) for i in range(len(xticks))]]
        )  # Initialize all labels as zero
        # Create plot widget and append to list
        plot = pg.PlotWidget(
            axisItems={"bottom": axis},
            labels={"left": "Volts (mV)"},
            title="Channel " + (str)(channels[i] + 1),
        )  # Create Plot Widget
        plot.plotItem.setMouseEnabled(x=False, y=False)  # Disable panning for widget
        plot.plotItem.showGrid(x=True)  # Enable vertical gridlines
        plots.append(plot)
        # Plot data and save curve. Append curve to list
        curve = plot.plot(
            x_vec, y_vec[i], pen=pg.mkPen(colors[i % len(colors)], width=0.5)
        )  # Set thickness and color of lines
        curves.append(curve)
        # Add plot to main widget
        layout.addWidget(plot, i, 0)

    # Display figure as a new window
    fig.show()

    # Print data to file
    if save:
        # Ensure savefile ends with .csv
        if savefile[-4:] == ".csv":
            savefile = savefile + ".csv"

        # Ensure the file doesn't exist already
        i = 1
        filename = savefile[-4:]
        while os.path.exists(savefile):
            savefile = filename + str(i) + ".csv"
            i += 1

        print("Printing to file ", savefile)

        # Create empty dataframe to store data
        d = dict(zip(channels, np.zeros(np.size(channels))))
        df = pd.DataFrame(data=d, index=[0])

    ###################################
    # Real-Time Plotting Loop
    ###################################

    firstUpdate = True
    while True:
        chunk = inlet.pull_chunk()

        if chunk:  # Check for available chunk
            chunkdata = np.transpose(
                chunk[0]
            )  # Get chunk data and transpose to be CHANNELS x CHUNKLENGTH
            chunkperiod = len(chunkdata[0]) * (1 / fs)
            xticks = [x - chunkperiod for x in xticks]  # Update location of x-labels

            if save:
                to_append = pd.Series(chunk[0][0], index=df.columns)
                df = df.append(to_append, ignore_index=True)

            # Update x-axis locations and labels
            if (
                xticks[0] < 0
            ):  # Check if a label has crossed to the negative side of the y-axis

                # Delete label on left of x-axis and add a new one on the right side
                xticks.pop(0)
                xticks.append(xticks[-1] + tickfactor)

                # Adjust time labels accordingly
                # Check to see if it's the first update, if so skip so that time starts at zero
                if not firstUpdate:
                    xlabels.append(xlabels[-1] + tickfactor)
                    xlabels.pop(0)
                else:
                    firstUpdate = False

            # Update plotted data
            for i in range(0, np.size(channels)):
                # Append chunk to the end of y_data
                y_vec[i] = np.append(y_vec[i], chunkdata[int(channels[i])], axis=0)[
                    len(chunkdata[int(channels[i])]) :
                ]
                curves[i].setData(x_vec, y_vec[i])  # Update data

                # Update x-axis labels
                axis = plots[i].getAxis(name="bottom")
                axis.setTicks(
                    [[(xticks[i], str(xlabels[i])) for i in range(len(xticks))]]
                )

        # Update QT Widget to reflect the changes we made
        pg.QtGui.QApplication.processEvents()

        # Check to see if widget if has been closed, if so exit loop
        if not fig.isVisible():
            break

    # Write the dataframe to file
    if save:
        with open(savefile, "w") as f:
            f.write(df.to_csv(index=False))

    # Close the stream inlet
    inlet.close_stream()

    return


def plotFreqDomain(
    stream_info, channels=None, size=(1500, 1500), title=None, measure="dB"
):
    """Plot Real-Time in the frequency domain using a static x-axis and changing y axis values.

    Accepts a pylsl StreamInlet Object and plots chunks in real-time as they are recieved
    using a pyqtgraph plot. Can plot multiple channels.

    Args:
        stream_info (pylsl StreamInfo Object): The stream info object for the stream to be plotted
        channels: The number of channels in the signal. Default (None) plots all channels
        fs (int): The sampling frequency of the device. If default (None) function will attempt to determine
            sampling frequency automatically
        size (array): Array of type (width, height) of the figure
        title (string): Title of the plot figure
        measure: the measurement unit to use when plotting. Can be one of the following,
            'dB' - Decibels
            'W/Hz' - Watts per Hz
            Default is decibels
    """
    #################################
    # Stream Inlet Creation
    #################################
    inlet = StreamInlet(stream_info, recover=True)
    inlet.open_stream()  # Stream is opened implicitely on first call of pull chunk, but opening now for clarity

    #################################
    # Variable Initialization
    #################################

    # Get list of channels to be plotted
    if channels is None:
        numchan = stream_info.channel_count()  # number of available channels
        channels = np.linspace(0, numchan - 1, numchan)
    else:
        channels = [
            x - 1 for x in channels
        ]  # Must shift channel numbers such that they represent indices

    for channel in channels:
        if (channel < 0) or (
            channel > (stream_info.channel_count() - 1)
        ):  # Must shift by one since channels holds indices
            print("""ERROR: Channel Number out of range""")
            return

    # Get chunkwidth of PSD stream
    window_length = int(stream_info.desc().child_value("nperseg"))
    # Note nperseg = window_length if periodogram method was used, if welch was use we set the window_length to nperseg
    chunkwidth = int(window_length / 2 + 1)

    # Get sampling frequency
    fs = stream_info.nominal_srate()

    ##################################
    # Figure and Plot Set Up
    ##################################

    # Initialize QT
    app = QtGui.QApplication([])

    # Define a top-level widget to hold everything
    fig = QtGui.QWidget()
    fig.resize(size[0], size[1])  # Resize window
    if title is not None:
        fig.setWindowTitle(title)  # Set window title
    layout = QtGui.QGridLayout()
    fig.setLayout(layout)

    # Set up initial plot conditions
    (x_vec, step) = np.linspace(
        0, int(fs / 2), chunkwidth, retstep=True
    )  # vector used to plot y values
    y_vec = np.zeros((np.size(channels), len(x_vec)))  # Initialize y_values as zero

    # Set Up subplots and lines
    plots = []
    curves = []
    colors = ["c", "m", "g", "r", "y", "b"]  # Color options for various channels
    for i in range(0, np.size(channels)):
        # Create plot widget and append to list
        plot = pg.PlotWidget(
            labels={"left": "Power (" + measure + ")"}, title="Channel " + (str)(i + 1)
        )  # Create Plot Widget
        plot.plotItem.setMouseEnabled(x=False, y=False)  # Disable panning for widget
        plot.plotItem.showGrid(x=True)  # Enable vertical gridlines
        plots.append(plot)
        # Plot data and save curve. Append curve to list
        curve = plot.plot(
            x_vec, y_vec[i], pen=pg.mkPen(colors[i % len(colors)], width=0.5)
        )  # Set thickness and color of lines
        curves.append(curve)
        # Add plot to main widget
        layout.addWidget(plot, np.floor(i / 2), i % 2)

    # Display figure as a new window
    fig.show()

    ###################################
    # Real-Time Plotting Loop
    ###################################

    buffer = []
    while True:
        chunk = inlet.pull_chunk()

        if not (np.size(chunk[0]) == 0):  # Check for available chunk
            chunkdata = chunk[0]  # Get chunk data
            if np.size(buffer) == 0:
                buffer = chunkdata
            else:
                buffer = np.append(buffer, chunkdata, axis=0)

        while np.size(buffer, 0) > chunkwidth:
            data = buffer[0:chunkwidth][:]
            buffer = buffer[chunkwidth:][:]
            data = np.transpose(data)  # transpose to be CHANNELS x CHUNKLENGTH

            # Update plotted data
            for i in range(0, np.size(channels)):
                if measure == "dB":
                    update = 10 * np.log10(data[int(channels[i])])
                elif measure == "W/Hz":
                    update = data[int(channels[i])]
                else:
                    print(
                        "ERROR: Unknown Measurement unit, please see documentation for available measurement units"
                    )
                    return

                curves[i].setData(x_vec, update)  # Update data

            # Update QT Widget to reflect the changes we made
            pg.QtGui.QApplication.processEvents()

        # Check to see if widget if has been closed, if so exit loop
        if not fig.isVisible():
            break

    # Close the stream inlet
    inlet.close_stream()

    return
