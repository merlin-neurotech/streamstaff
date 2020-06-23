import numpy as np
from pylsl import StreamInlet, StreamOutlet
from scipy import signal
from templates import StreamManipulator


class custom_filter(StreamManipulator):
    def __init__(
        self,
        input_stream,
        stream_type="filter",
        output_stream_name="default",
        channels=None,
        filter_type="butter",
        sample_period=5,
        window_length=256,
        buf_size=128,
    ):
        """Takes a time series stream as an input and creates a filtered output stream.

        Args:
            input_stream (pylsl StreamInfo Object): The stream which you want 
                to filter
            stream_type (str): The type of the output stream. Defaults to 
                'filter'
            output_stream_name (str): The desired name of the output stream. 
                Defaults to None. If the default value is kept, the output stream 
                name will be the name of the input stream with the 'stream_type' 
                appended.
            channels (list): A list of integers which represent which channels 
                to convert. Default (None) will include all available channels 
            sample_period (int): The sampling period, in seconds, to be used when applying the chosen filter. Defaults to 5.
            window_length (int): The length of the window, in samples, to take when converting the signal to the frequency domain. 
                This function uses an N-point FFT where N is window_length
            buf_size (int): The buffer use to hold signal. Defaults to 128 and should be between 128 and 1024.  
        """

        if stream_type == "filter":
            stream_type = "_".join([filter_type, stream_type])

        kwargs = dict(
            filter_type=filter_type,
            sample_period=sample_period,
            window_length=window_length,
            buf_size=buf_size,
        )

        super().__init__(
            input_stream,
            stream_type=stream_type,
            output_stream_name=output_stream_name,
            channels=channels,
            **kwargs,
        )

    def initialize_output_stream(self):
        super().init_output_stream()

        self.meta.append_child_value("window_length", str(self.window_length))

    def _backend(self, **kwargs):
        inlet = StreamInlet(self.input_stream, recover=True)
        inlet.open_stream()

        outlet = StreamOutlet(self.output_stream)

        # Sampling frequency of signal
        fs = self.input_stream.nominal_srate()
        # Nyquist sampling frequency
        fs_nyquist = 0.5 * fs
        # Total number of samples
        n = int(self.sample_period * fs)  # total number of samples
        # Signal frequency
        signal_frequency = fs / (self.sample_period ** 2)
        cutoff = np.ceil(signal_frequency)

        buffer = np.empty((0, 5))

        while True:
            input_chunk = inlet.pull_chunk()  # Pull Chunk

            if input_chunk[0] and np.shape(input_chunk)[1] > 0:
                # Check for available chunk
                buffer = np.append(buffer, input_chunk[0], axis=0)

                if len(buffer) >= self.buf_size:
                    # Take data from buffer
                    data = buffer[0 : self.buf_size]
                    buffer = buffer[self.buf_size :]
                    data = np.transpose(data)

                    # Calculate filtered output for desired channels
                    output = []
                    order = 2
                    for i in range(0, np.size(channels)):
                        if self.filter_type == "butter":
                            normal_cutoff = cutoff / fs_nyquist

                            b, a = signal.butter(order, normal_cutoff)

                            y = signal.filtfilt(b, a, data[i])
                            output.append(y)
                        else:
                            raise ValueError("Incorrect filter_type specified")

                    output = np.transpose(output)
                    output = output.tolist()

                outlet.push_chunk(output)
