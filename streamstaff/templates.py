import threading

import numpy as np
from pylsl import StreamInfo, StreamInlet, StreamOutlet


class StreamManipulator(object):
    def __init__(
        self,
        input_stream,
        stream_type="default",
        output_stream_name="default",
        channels=None,
        **kwargs
    ):
        self.input_stream = input_stream
        self.stream_type = stream_type

        if channels is None:
            # number of available channels
            self.numchan = self.input_stream.channel_count()
            self.channels = np.linspace(0, self.numchan - 1, self.numchan)
        else:
            self.channels = channels
            self.numchan = int(np.size(self.channels))

        for key in kwargs.keys():
            setattr(self, key, kwargs.get(key))

        if output_stream_name == "default":
            self.output_stream_name = str(self.input_stream.name()) + "--" + stream_type
        else:
            self.output_stream_name = output_stream_name

        self.initialize_output_stream()

        thread = threading.Thread(target=self._backend, daemon=True,)
        thread.start()

    def initialize_output_stream(self):
        self.output_stream = StreamInfo(
            name=self.output_stream_name,
            type=self.stream_type,
            channel_count=self.numchan,
            nominal_srate=self.input_stream.nominal_srate(),
            channel_format="float32",
            source_id=self.input_stream.source_id(),
        )

        self.meta = self.output_stream.desc()
        self.fs = self.input_stream.nominal_srate()

    def _backend(self):
        inlet = StreamInlet(self.input_stream, recover=True)
        inlet.open_stream()

        outlet = StreamOutlet(self.output_stream)

        while True:
            chunk = inlet.pull_chunk()

            if chunk[0] and len(chunk) > 0:
                outlet.push_chunk(chunk)
