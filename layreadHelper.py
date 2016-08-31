
def cleanAnnotations(header):
    """ cleanAnnotations(header)
    Prints all the annotations in the header of a Persyst lay/dat file in a somewhat cleaned format.
    Uninteresting annotations (e.g., 'XLSpike') are ignored.

     Input:
       header - produced by layread.py from a Persyst lay/dat file

     Output:
       none
    """
    if len(header['annotations'])==0:
        print('No annotations in header.')
    else:
        ignoreList=['XLEvent',
                   'XLSpike',
                   'Video Recording OFF',
                   'Video Recording ON',
                   'Stop Recording',
                   'Start Recording',
                   'Recording Analyzer - XLSpike - Intracranial',
                   'Recording Analyzer - XLEvent - Intracranial',
                   'Recording Analyzer - CSA',
                   'Started Analyzer - XLSpike - Intracranial',
                   'Started Analyzer - CSA']
        print('*** Start Time: {} ***'.format(header['starttime']))
        for anEvent in header['annotations']:
            if anEvent['text'][:-1] not in ignoreList:
                print('{}, {}: dur={}'.format(anEvent['text'][:-1],anEvent['time'],anEvent['duration']))
        lastAnnotation=header['annotations'][-1]
        print('*** Last Annotation at: {} ***'.format(lastAnnotation['time']))