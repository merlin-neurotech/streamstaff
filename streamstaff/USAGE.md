# USAGE
Example usage of the filtering and transforms using the new class based implementation is shown below.

```
import ble2lsl
import plotting
import pylsl
from ble2lsl.devices import muse2016
from filtering import custom_filter
from transforms import psd

dummy_streamer = ble2lsl.Dummy(muse2016)
stream_info = pylsl.resolve_byprop("type", "EEG")
stream = stream_info[0]

fourier = psd(input_stream=stream)
plotting.plotFreqDomain(fourier.output_stream)

lowpass_butter = custom_filter(
    input_stream=stream, stream_type="butterworth-filter", filter_type="butter"
)
plotting.plotTimeDomain(lowpass_butter)

plotting.plotTimeDomain(stream)
```
