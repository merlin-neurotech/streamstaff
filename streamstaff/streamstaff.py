import pylsl as pl 


def getStream_info(device, max_chunk = 0, max_chunkln = 12, stream_type = 'EEG'):
    """ Gets the stream info object from the Ble-2lsl Streamer object

    resolves the streamer object using resolve_byprop and returns the stream info object from the resolved stream

    Args:
        device (Ble-lsl Streamer object): the Ble-lsl device made by the user
        max_chunk (int): is the max chunk length for the given Streamer object 
        max_chunkln (int): is the max length of the chunks that the stream pulls 
        stream_type (string): is the type of data that is being streamed

    Returns: 
        info (info object): the stream info object from the given stream
    """
    stream = pl.resolve_byprop('type', stream_type, timeout= 2)
    if len(stream) == 0:
        raise RuntimeError("no {} stream found".format(stream_type))
    print(type(stream))
    return stream[0]


    #threading will also be in this python file 

