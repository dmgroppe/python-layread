import inifile
import numpy as np
import pdb,traceback,sys
import time
import os
from time import mktime
from datetime import datetime

def layread(layFileName,datFileName=None,timeOffset=0,timeLength=-1):
    """
    Required Input:
        layFileName - the .lay file name (including path)

    Optional Inputs:
        datFileName - the .dat file name. Default: assume the same path and file stem as layFileName
        timeOffset - the number of time steps to ignore (so if this was set to 3 for example, the file reader would extract data for time steps 4 to the end)
        timeLength - the number of time steps to read (so if this was set to 5 and timeOffset was set to 3, the file reader would read data for time steps 4,5,6,7,8). If this parameter is set to -1, then the whole .dat file is read.

    default values:
        timeOffset=0 (i.e., start reading that beginning of the file)
        timeLength=-1 (i.e., read in entire file)

    outputs:
        header - information from .lay file. It contains the following keys:
            samplingrate: sampling rate in Hz
            rawheader: a dict of the raw header from the lay file
            starttime: string indicating the start time of recording (date hours:min:seconds)
            datafile: full path and filename of dat file
            annotations: list of event annotations
            waveformcount: # of channels
            patient: dict of patient information (mostly empty)
        record - EEG data from .dat file (channel x time numpy array)
    """

    # takes ~8 min for a 1.5GB file
    t = time.time()

    # If datFileName not specified, assume it is the same location and has the same stem as layFileName
    if datFileName==None:
        layPath = os.path.dirname(layFileName)
        layFname = os.path.splitext(os.path.basename(layFileName))
        datFileName = os.path.join(layPath, layFname[0] + '.dat')

    # get .ini file and replace [] with ''
    data, sections, subsections = inifile.inifile(layFileName,'readall') # sections and subsections currently unused
    for row in data:
        for entry in row:
            if entry == []:
                entry = ''

    # find fileinfo section of .lay file and map to correct .dat file
    fileInfoArray = []
    for row in data:
        if row[2] == 'file':
            row[3] = datFileName
        if row[0] == 'fileinfo':
            fileInfoArray.append(row)

    # fileinfo
    fileinfo = {} # dictionary
    for row in fileInfoArray:
        fileinfo[row[2]] = row[3]

    # patient
    patient = {} # dictionary
    for row in data:
        if row[0] == 'patient':
            patient[row[2]] = row[3]

    # montage
    montage = {} # dictionary
    for row in data:
        if row[0] == 'montage':
            montage_data = [] # 2d nested list
            for row_ in data:
                if row[2] == row_[0]:
                    montage_data.append([row_[2],row_[3]])
            montage[str(row[2])] = montage_data

    # sampletimes
    sampletimes = [] # list of dictionaries
    for row in data:
        if row[0] == 'sampletimes':
            #print("sample: {}, time: {}".format(float(row[2]),float(row[3])))
            sampletimes.append({'sample':float(row[2]),'time':float(row[3])})
    # Persyst appears to periodically resync the time-sample mapping. sampletimes tells you when those happen.
    # For example, in a short demo files with 256 Hz sampling I get
    # sample: 0.0, time: 34273.799
    # sample: 454540.0, time: 36049.344
    # sample: 907040.0, time: 37816.922

    # channelmap
    channelmap = [] # list of strings
    for row in data:
        if row[0] == 'channelmap':
            channelmap.append(row[2])

    # move some info from raw header to header
    header = {} # dictionary
    if len(fileInfoArray) > 0:
        # checking individual fields exist before moving them
        if 'file' in fileinfo:
            header['datafile'] = fileinfo['file']
        if 'samplingrate' in fileinfo:
            header['samplingrate'] = int(fileinfo['samplingrate'])
        if 'waveformcount' in fileinfo:
            header['waveformcount'] = int(fileinfo['waveformcount'])
    # NOT IMPLEMENTED dn = datenum(strcat(date, ',', time));
    date = patient['testdate'].replace('.','/')
    tim = patient['testtime'].replace('.',':')
    dt = time.strptime(date + ',' + tim,'%m/%d/%y,%H:%M:%S')
    dt = datetime.fromtimestamp(mktime(dt))
    dt = dt.strftime('%d-%b-%Y %H:%M:%S') # convert date and time to standard format
    header['starttime'] = dt
    header['patient'] = patient

    # comments
    try:
        lay_file_ID = open(layFileName,'r')
    except:
        raise Exception('Error in open: file not found')
    comments_ = 0
    cnum = 0
    comments = [] # list of strings
    annotations = [] # list of dictionaries
    for tline in lay_file_ID:
        if 1 == comments_:
            contents = tline.split(',')
            if len(contents) < 5:
                break # there are no more comments
            elif len(contents) > 5:
                separator = ','
                contents[4] = separator.join(contents[4:len(contents)])
            # raw header contains just the original lines
            comments.append(tline.strip()) # These lines look something like this:
            # 127.182,0.000,0,100,XLSpike
            # This first element (in this case 127.182) indicates the time in seconds from the start of the file at which
            # the event occurred
            samplenum = float(contents[0])*float(fileinfo['samplingrate']) # convert onset from seconds to samples
            samplenumRaw=samplenum
            i = 0
            while i < len(sampletimes)-1 and samplenum > sampletimes[i+1]['sample']:
                # i tells you which sample-synchronization point to use in order to map from samples to time
                i=i+1
            samplenum -= sampletimes[i]['sample']
            samplesec = samplenum / float(fileinfo['samplingrate'])
            timesec = samplesec + sampletimes[i]['time']
            commenttime = time.strftime('%H:%M:%S',time.gmtime(timesec)) # should be converted to HH:MM:SS
            dn = patient['testdate'] + ',' + str(commenttime)
            dn = time.strptime(dn,'%m/%d/%y,%H:%M:%S')
            dn = datetime.fromtimestamp(mktime(dn))
            dn = dn.strftime('%d-%b-%Y %H:%M:%S') # convert date and time to standard format
            annotations.append({'time':dn, 'sample': int(np.round(samplenumRaw)),'duration':float(contents[1]),'text':contents[4]})
            # annotations[cnum] = {'time':dn} # previously datetime(dn,'ConvertFrom','datenum')
            # annotations[cnum] = {'duration':float(contents[1])}
            # annotations[cnum] = {'text':contents[4]}
            cnum += 1
        elif tline[0:9] == '[Comments]'[0:9]:
            # read until get to comments
            comments_ = 1
    lay_file_ID.close()

    header['annotations'] = annotations # add to header dictionary
    rawhdr = {} # dictionary to represent rawhdr struct
    rawhdr['fileinfo'] = fileinfo
    rawhdr['patient'] = patient
    rawhdr['sampletimes'] = sampletimes
    rawhdr['channelmap'] = channelmap
    rawhdr['comments'] = comments
    rawhdr['montage'] = montage
    header['rawheader'] = rawhdr # put raw header in header

    # dat file
    try:
        dat_file_ID = open(datFileName,'rb')
    except:
        raise Exception('Error in open: file not found')
    recnum = float(rawhdr['fileinfo']['waveformcount'])
    recnum = int(recnum)
    calibration = float(rawhdr['fileinfo']['calibration'])
    if int(rawhdr['fileinfo']['datatype']) == 7:
        precision = np.int32
        dat_file_ID.seek(recnum*4*timeOffset,1)
    else:
        precision = np.int16
        dat_file_ID.seek(recnum*2*timeOffset,1)

    # read data from .dat file into array of correct size, then calibrate
    # records = recnum rows x inf columns
    if timeLength == -1:
        toRead = -1 # elements of size precision to read
    else:
        toRead = timeLength*recnum
    record = np.fromfile(dat_file_ID,dtype=precision,count=toRead)
    dat_file_ID.close()
    record = record * calibration # explicit
    record = np.reshape(record,(recnum,-1),'F') # recnum rows
    record = record.astype(np.float32) # cast as float32; more than enough precision

    # elapsed time (in min)
    elapsed = (time.time() - t) / 60

    return (header,record)

# if __name__ == '__main__':
# 	try:
# 		layread("\Users\Ian\Documents\Adaptive Stimulation\FileReader\skAnonShort.lay","\Users\Ian\Documents\Adaptive Stimulation\FileReader\skAnonShort.dat") # sample lay and dat files i was using
# 	except:
# 		type,value,tb = sys.exc_info()
# 		traceback.print_exc()
# 		pdb.post_mortem(tb)