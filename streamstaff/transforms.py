import threading

import numpy as np
from pylsl import StreamInfo, StreamInlet, StreamOutlet
from scipy import signal

##########################
# Backend Functions
##########################


def psd_backend(
    input_stream,
    output_stream,
    channels=None,
    method="periodogram",
    window_length=256,
    window_type=np.hamming,
    nperseg=None,
    noverlap=None,
):
    """The backend function for psd. 
    This function takes in time domain chunks and converts them to psd chunks within an infinite loop. See documentation of
    psd function for argument descriptions
    """
    #################################
    # Setup
    #################################

    # Create stream inlet
    inlet = StreamInlet(input_stream, recover=True)
    inlet.open_stream()  # Stream is opened implicitely on first call of pull chunk, but opening now for clarity

    # Create StreamOutlet to push data to output stream
    outlet = StreamOutlet(output_stream)

    # Get number of channels to transform
    if channels is None:
        numchan = input_stream.channel_count()
        channels = np.linspace(0, numchan - 1, numchan)
    else:
        channels = [
            x - 1 for x in channels
        ]  # Must shift channel numbers such that they represent indices

    ###################################
    # Calculate PSD
    ###################################

    buffer = np.empty(
        (0, 5)
    )  # Buffer to hold signal and extract segments with window_length samples
    fs = input_stream.nominal_srate()  # Sampling frequency of signal

    while True:
        input_chunk = inlet.pull_chunk()  # Pull Chunk

        if input_chunk[0] and np.shape(input_chunk)[1] > 0:  # Check for available chunk
            buffer = np.append(buffer, input_chunk[0], axis=0)

            if len(buffer) >= window_length:
                # Take data from buffer
                data = buffer[0:window_length]
                buffer = buffer[window_length:]
                data = np.transpose(data)

                # Calculate PSD for desired channels
                psd = []
                for i in range(0, np.size(channels)):

                    # Get FFT
                    if method == "periodogram":
                        # Calculate window
                        window = window_type(
                            window_length
                        )  # Window to multiply signal by

                        # Calculate power of window so that it can be used to normalize data when converting to PSD
                        window_power = np.sum(np.square(window))

                        # Multiply data by window
                        data_windowed = data[int(channels[i])] - np.mean(
                            data[int(channels[i])], axis=0
                        )
                        data_windowed = data_windowed * window

                        # Calculate the fft
                        data_fft = np.fft.rfft(data_windowed, n=window_length, axis=0)

                        # Convert FFT to PSD
                        psd.append(
                            (1 / window_power) * np.square(abs(data_fft))
                        )  # Using periodogram method where you normalize by window power

                    elif method == "welch":
                        # Calculate window, has shorter length since welch uses segments to calc PSD
                        if nperseg is None:
                            # Default is to have 8 segments
                            window = window_type(int(window_length / 8))
                        else:
                            window = window_type(nperseg)

                        f, pxx = signal.welch(
                            data[i], fs=fs, noverlap=noverlap, window=window
                        )

                        psd.append(pxx)

                psd = np.transpose(psd)
                psd = psd.tolist()

                # Push fft transform for each channel using outlet
                outlet.push_chunk(psd)


##########################
# Wrapper Functions
##########################


def psd(
    input_stream,
    output_stream_name="default",
    method="periodogram",
    window_length=256,
    window_type=np.hamming,
    channels=None,
    nperseg=None,
    noverlap=None,
):
    """Takes a time series stream as an input and outputs power spectral density (PSD) stream.

    Args:
        input_stream (pylsl StreamInfo Object): The stream which you want to convert into the frequency domain (PSD)
        output_stream_name (str): The desired name of the output stream. Default is the name of the input stream with '-PSD' appended
        method (str): The method to use when calculating the PSD. Can be one of the following,
            'periodogram'
            'welch'
            Note that the welch method is better for signals with a high sampling rate
        window_length (int): The length of the window, in samples, to take when converting the signal to the frequency domain.
            This function uses an N-point FFT where N is window_length
        window_type (window function): The window type to use before applying the FFT. The default is a hamming window.
            Should be in the form of a window function where window_type(window_length) results in an array with window values.
            All the numpy window functions will work as an input for the parameter
        channels (list): A list of integers which represent which channels to convert. Default (None) will include
            all available channels in the PSD stream
        nperseg (int): Only used if the welch method is selected. The number of samples to use in each segment when converting stream to psd
            Should also be a power of 2. Default is the sampling frequency/8 such that there are 8 segments per window
        noverlap: Only used if welch method is selected. The number of samples to overlap each segment
  
    Returns:
        output_stream (pylsl StreamInfo Object): A stream of type 'PSD' generated from the input stream

    """

    #################################
    # Create New Output StreamInfo Objectcd
    #################################

    # Set Default Output Stream Name
    if output_stream_name == "default":
        output_stream_name = str(input_stream.name() + "-PSD")

    # Get number of channels to transform
    if channels is None:
        numchan = input_stream.channel_count()  # number of available channels
    else:
        numchan = int(np.size(channels))

    # Create Output StreamInfo Object
    output_stream = StreamInfo(
        name=output_stream_name,
        type="PSD",
        channel_count=numchan,
        nominal_srate=input_stream.nominal_srate(),
        channel_format="float32",
        source_id=input_stream.source_id(),
    )

    # Add important metadata to stream
    meta = output_stream.desc()
    meta.append_child_value("window_length", str(window_length))

    # If welch method was used, window length is actually the length of each segment
    if method == "welch":
        if nperseg is None:
            meta.append_child_value("nperseg", str(int(window_length / 8)))
        else:
            meta.append_child_value("nperseg", str(nperseg))
    else:
        meta.append_child_value("nperseg", str(window_length))

    ####################################
    # Create Thread to Run psd_backend
    ####################################

    thread = threading.Thread(
        target=psd_backend,
        daemon=True,
        kwargs=dict(
            input_stream=input_stream,
            output_stream=output_stream,
            channels=channels,
            method=method,
            window_length=window_length,
            window_type=window_type,
            nperseg=nperseg,
            noverlap=noverlap,
        ),
    )

    #  Start thread and return output stream
    thread.start()

    return output_stream
