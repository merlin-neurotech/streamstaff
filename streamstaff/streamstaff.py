import pylsl as pl 


def get_stream_info(prop='type', value='EEG', index=0):
    """ Gets the stream info object from the Ble-2lsl Streamer object

    resolves the streamer object using one of it's properties and returns the stream info object.
    If more than 1 stream is resolved/found, the default is to return the first one

    Args:
        prop (str): The property to use in order to find the stream. (eg. 'name', 'type', 'source_id' etc.)
        value (str): Value of the property (eg. 'PSD' or 'EEG' for type)
        index (int): If expecting more than one stream to be resolved, the index in the list of the one to choose

    Returns: 
        stream_info (stream_info object): the stream info object from the resolved stream
    """
    # Resolve stream using a property of the stream
    stream = pl.resolve_byprop(prop, value, timeout= 2)
    if len(stream) == 0:
        raise RuntimeError("no {} stream found".format(value))
    if len(stream) < index+1:
        raise RuntimeError('index set to ' + str(index) + ' however only ' + str(len(stream)) + ' streams found')
    
    return stream[index]


    #threading will also be in this python file 

