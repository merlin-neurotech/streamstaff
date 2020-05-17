import numpy as np
from pylsl import StreamInfo, StreamInlet, StreamOutlet
from templates import StreamManipulator


class psd(StreamManipulator):
    def __init__(
        self,
        input_stream,
        stream_type="psd",
        output_stream_name="default",
        channels=None,
        method="periodogram",
        window_length=256,
        window_type=np.hamming,
        nperseg=None,
        noverlap=None,
    ):
        """Takes a time series stream as an input and creates an power spectral density (PSD) stream.

        Args:
            input_stream (pylsl StreamInfo Object): The stream which you want to convert into the frequency domain (PSD)
            stream_type (str): The type of the output stream. Defaults to 
                'psd'
            output_stream_name (str): The desired name of the output stream. 
                Defaults to None. If the default value is kept, the output stream 
                name will be the name of the input stream with the 'stream_type' 
                appended.
            channels (list): A list of integers which represent which channels 
                to convert. Default (None) will include all available channels 
            method (str): The method to use when calculating the PSD. Can be one of the following,
                'periodogram'
                'welch'
                Note that the welch method is better for signals with a high sampling rate
            window_length (int): The length of the window, in samples, to take 
                when converting the signal to the frequency domain. This 
                function uses an N-point FFT where N is window_length
            window_type (window function): The window type to use before 
                applying the FFT. The default is a hamming window. Should be in
                the form of a window function where window_type(window_length) 
                results in an array with window values. All the numpy window 
                functions will work as an input for the parameter
            nperseg (int): Only used if the welch method is selected. The 
                number of samples to use in each segment when converting stream
                to psd. Should also be a power of 2. Default is the sampling 
                frequency/8 such that there are 8 segments per window
            noverlap: Only used if welch method is selected. The number of 
                samples to overlap each segment
        """

        kwargs = dict(
            method=method,
            window_length=window_length,
            window_type=window_type,
            nperseg=nperseg,
            noverlap=noverlap,
        )
        super().__init__(
            input_stream,
            stream_type=stream_type,
            output_stream_name=output_stream_name,
            channels=channels,
            **kwargs
        )

    def init_output_stream(self):
        super().init_output_stream()
        self.meta.append_child_value("window_length", str(self.window_length))

        if self.method == "welch":
            if self.nperseg is None:
                self.meta.append_child_value(
                    "nperseg", str(int(self.window_length / 8))
                )
            else:
                self.meta.append_child_value("nperseg", str(self.nperseg))
        else:
            self.meta.append_child_value("nperseg", str(self.window_length))

    def _backend(self, **kwargs):
        inlet = StreamInlet(self.input_stream, recover=True)
        inlet.open_stream()

        outlet = StreamOutlet(self.output_stream)

        buffer = np.empty((0, self.numchan))

        while True:
            chunk = inlet.pull_chunk()

            if chunk[0] and len(chunk) > 0:
                buffer = np.append(buffer, chunk[0], axis=0)
                if len(buffer) >= self.window_length:
                    # Take data from buffer
                    data = buffer[0 : self.window_length]
                    buffer = buffer[self.window_length :]
                    data = np.transpose(data)

                    # Calculate PSD for desired channels
                    psd = []
                    for i in range(0, self.numchan):

                        # Get FFT
                        if self.method == "periodogram":
                            # Calculate window
                            window = self.window_type(self.window_length)

                            # Calculate power of window so that it can be used to normalize data when converting to PSD
                            window_power = np.sum(np.square(window))

                            # Multiply data by window
                            data_windowed = data[int(self.channels[i])] - np.mean(
                                data[int(self.channels[i])], axis=0
                            )
                            data_windowed = data_windowed * window

                            # Calculate the fft
                            data_fft = np.fft.rfft(
                                data_windowed, n=self.window_length, axis=0
                            )

                            # Convert FFT to PSD
                            # Using periodogram method where you normalize by window power
                            psd.append((1 / window_power) * np.square(abs(data_fft)))

                        elif self.method == "welch":
                            # Calculate window, has shorter length since welch uses segments to calc PSD
                            if self.nperseg is None:
                                # Default is to have 8 segments
                                window = self.window_type(int(self.window_length / 8))
                            else:
                                window = self.window_type(self.nperseg)

                            f, pxx = signal.welch(
                                data[i],
                                fs=self.fs,
                                noverlap=self.noverlap,
                                window=self.window,
                            )

                            psd.append(pxx)

                    psd = np.transpose(psd)
                    psd = psd.tolist()

                    # Push fft transform for each channel using outlet
                    outlet.push_chunk(psd)
