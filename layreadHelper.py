
def cleanAnnotations(header):
    """ cleanAnnotations(header)
    Prints all the annotations in the header of a Persyst lay/dat file in a somewhat cleaned format.
    Uninteresting annotations (e.g., 'XLSpike') are ignored.

     Input:
       header - produced by layread.py from a Persyst lay/dat file

     Output:
       none
    """

    cleanList=[]
    if len(header['annotations'])==0:
        print('No annotations in header.')
    else:
        ignoreList=['XLEvent',
                    'XLSpike',
                    'Video Recording ON',
                    'Video Recording OFF',
                    'Stop Recording',
                    'Start Recording',
                    'Recording Analyzer - XLSpike - Intracranial',
                    'Recording Analyzer - XLEvent - Intracranial',
                    'Recording Analyzer - CSA',
                    'Started Analyzer - XLSpike - Intracranial',
                    'Started Analyzer - CSA']
        print('*** Start Time: {} ***'.format(header['starttime']))
        for anEvent in header['annotations']:
            anEvent['text']=anEvent['text'][:-1] # get rid of carriage return at end of string
            if anEvent['text'] not in ignoreList:
                cleanList.append(anEvent)
                print('{}, {}: sample={}, dur={}'.format(anEvent['text'],anEvent['time'],
                                                         anEvent['sample'],anEvent['duration']))
        lastAnnotation=header['annotations'][-1]
        print('*** Last Annotation at: {} ***'.format(lastAnnotation['time']))

    return cleanList