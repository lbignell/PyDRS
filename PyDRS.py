import ctypes
import json
import time,sys,os
import pandas as pd
import numpy as np
import datetime, time
import matplotlib.pyplot as plt
import tables
sofile=os.path.join(os.path.dirname(os.path.realpath(__file__)),"libdrs.so")
so=ctypes.CDLL(sofile)
f1024=ctypes.c_float * 1024

class PyDRS:
    def __init__(self):
        self.drs=so.drs_create()
        self.paramdict = {'freq_GHz': 0.7, 
                      'isTransparent': True,
                      'TrigLevels_V': [-0.03]*4,
                      'isNegTrigPolarity': True,
                      'isRandomTriggers': False,
                      'TrigDelay_ns': 1500,
                      'TrigSource_OR': [True,False,False,False],
                      'TrigSource_AND':[False]*4,
                      'isDominoDuringReadout': False,
                      'RangeCentre_V': 0.0,
                      'isExtTrig': False #TODO: include ext in trig logic.
                      }
        self.comments = ''
        n=so.drs_getNumberOfBoards(self.drs)
        if 1 !=n:
             "# of DRS board should be 1, %d"%n
             return

        print "Serial: %d"%so.drs_getBoardSerialNumber(self.drs),
        print "Firmware: %d"%so.drs_getFirmwareVersion(self.drs),
        print "Board type: %d"%so.drs_getBoardType(self.drs)
        so.drs_init(self.drs)
        #so.drs_enableTcal(self.drs,1)  ### what does this function do? 
        
    def __del__(self):
       so.drs_delete(self.drs)

    def set_params(self):
        self.set_freq(self.paramdict['freq_GHz'])
        self.set_input_range(self.paramdict['RangeCentre_V'])
        self.set_trigger_proper()
        return

    def set_input_range(self,offset=0.0):
        '''
        Set centre of input range in V.
        Data are +/- 1 V about this value.
        '''
        if not so.drs_setInputRange(self.drs,
                ctypes.c_double(offset)):
            print('drs_setInputRange not set')
        return
        
    def set_freq(self,freq):
        '''
        Set the domino sampling frequency (GHz)
        '''
        if not so.drs_setFrequency(self.drs,
                ctypes.c_double(freq),True):
            print('drs_setFrequency not set!')
        return
   
    def set_domino_active(self):
        '''
        Set domino as running/not running during readout.
        '''
        if not so.drs_setDominoActive(self.drs, 
            self.paramdict['isDominoDuringReadout']):
            print("set_domino_active: NOT SET!")
        return

    def _calc_trig_mask(self):
        '''
        Convert the trigger bit mask to int, given the params.
        '''
        #TODO: work out whether you can actually do simultaneous
        # AND and OR of inputs.
        ands = self.paramdict['TrigSource_AND']
        ors = self.paramdict['TrigSource_OR']
        if np.any(ands) and np.any(ors):
            print("ERROR: can't set OR and AND mask concurrently!")
            return 0
        elif not np.any(ands) and not np.any(ors):
            print("ERROR: no trigger channel is selected!")
        else:
            #Return integer corresponding to the bit mask
            return sum(1<<i for i, b in enumerate(ors+ands) if b)

    def set_trigger_proper(self):
        '''
        Set the trigger, allowing for possible OR or AND on inputs.
        '''
        try:
            if not self.paramdict['isRandomTriggers']:
                #TODO: Include ext in trig logic.
                if self.paramdict['isExtTrig']:
                    if not so.drs_enableTrigger(self.drs, 1,1):
                        print("drs_enableTrigger not set!")
                else:
                    #Transparent mode is needed for analog trig
                    if not so.drs_setTranspMode(self.drs, 1):
                        print('drs_setTranspMode not set!')
                    if not so.drs_enableTrigger(self.drs,1,1):
                        ##lemo off, analog trigger on
                        print('drs_enableTrigger not set!')
                    tmask = self._calc_trig_mask()
                    if tmask == 0:
                        print("TRIGGER NOT SET!")
                        return
                    if not so.drs_setTriggerSource(self.drs, 
                            ctypes.c_ushort(tmask)):
                        print('drs_setTriggerSource not set!')
                    for ch, lvl in enumerate(self.paramdict['TrigLevels_V']):
                        if so.drs_setIndividualTriggerLevel(self.drs, ch, ctypes.c_double(lvl)) < 0:
                            print('drs_setIndividualTriggerLevel\
                                    not set!')

                    if not so.drs_setTriggerPolarity(self.drs,
                            self.paramdict['isNegTrigPolarity']):
                        print('drs_setTriggerPolarity not set!')
                    if not so.drs_setTriggerDelayNs(self.drs,
                            self.paramdict['TrigDelay_ns']):
                        print('drs_setTriggerDelayNs not set')
                    return
        
        except KeyError as err:
            wrongkey = err.args[0]
            print("Error: the parameter dictonary doesn't contain \
                    the key {0}. Trigger NOT set!".format(wrongkey))
            return

    def set_trigger(self,ch=1,level=0.05,pol=False,delay=0):
        if ch==0:
            ## lemo
            so.drs_enableTrigger(self.drs,1,0)
        else:
            ## ch
            so.drs_setTranspMode(self.drs,1)      ## enable transparent mode needed for analog trigger
            so.drs_enableTrigger(self.drs,0,1)    ##lemo off, analog trigger on
            so.drs_setTriggerSource(self.drs,ch-1)
        so.drs_setTriggerLevel(self.drs,ctypes.c_double(level))   ## in volte        
        so.drs_setTriggerPolarity(self.drs,pol)                 ## Falsepositive edge
        so.drs_setTriggerDelayNs(self.drs,delay)                ## 
        
    def measure(self,chs=[1],timeout=10000, softtrig=False):
        so.drs_startDomino(self.drs)
        if not softtrig:
            i=0
            #print("waiting for trigger...")
            while i< timeout:
                if so.drs_isBusy(self.drs)==0:
                    break
                time.sleep(0.001)
                i+=1
                if i%1000 == 0:
                    print('{0} sec without a trigger...'.format(i/1000))
            if i==timeout:
                print "measure() timeout!!"
        else:
            so.drs_softTrigger(self.drs)
        so.drs_transferWaves(self.drs,0,8)  ## TODO give optimal number
        ret=[]
        for i,ch in enumerate(chs):
            ret.append([f1024(),f1024()])
            tc=so.drs_getTriggerCell(self.drs,0)
            so.drs_getTime(self.drs,0, 2*(ch-1),tc,ret[i][0])
            so.drs_getWave(self.drs,0, 2*(ch-1), ret[i][1])
        return ret

    def get_true_freq(self):
        '''
        Return the True sampling frequency in GHz.
        '''
        so.drs_getTrueFrequency.restype = ctypes.c_double
        return so.drs_getTrueFrequency(self.drs)

    def get_nominal_freq(self):
        '''
        Return the nominal sampling frequency in GHz.
        '''
        so.drs_getNominalFrequency.restype = ctypes.c_double
        return so.drs_getNominalFrequency(self.drs)

    def get_trig_delay(self):
        '''
        Return the trigger delay in ns.
        '''
        so.drs_getTriggerDelayNs.restype = ctypes.c_double
        return so.drs_getTriggerDelayNs(self.drs)

    def get_scaler(self, channel):
        '''
        Return the scaler count for channel.
        '''
        so.drs_getScaler.restype = ctypes.c_uint
        return so.drs_getScaler(self.drs, int(channel))

    def run_and_save(self, nevents, fname, chns=[1,2,3,4], updateN=1000, thepipe=None):
        '''
        Acquire nevents waveforms and store in fname as HDF5 file.
        '''
        retarr = np.array([])
        #Acquire 1 sample to test.
        ret = np.array(self.measure(chs=chns))
        h5file = tables.openFile(fname, mode='a')
        chndepth = so.drs_getChannelDepth(self.drs)
        #lzo is a good tradeoff btw compression and speed.
        compfilter = tables.Filters(complevel=1, complib='lzo')
        timegroup = h5file.createEArray(h5file.root, 'time',
                tables.Atom.from_dtype(ret[:,0,:].dtype),
                shape=(0, ret[:,0,:].shape[0], ret[:,0,:].shape[1]),
                filters=compfilter, expectedrows=chndepth)
        wfmgroup = h5file.createEArray(h5file.root, 'wfms',
                tables.Atom.from_dtype(ret[:,1,:].dtype),
                shape=(0, ret[:,1,:].shape[0], ret[:,1,:].shape[1]),
                filters=compfilter, expectedrows=chndepth)
        metaarr = h5file.create_array(h5file.root, "run_info", [self.comments, json.dumps(self.paramdict)], 'run_info')
        timegroup.append(ret[:,0,:][None])
        wfmgroup.append(ret[:,1,:][None])
        for i in range(nevents-1):
            if not thepipe is None:
                if thepipe.poll():
                    cmd = thepipe.recv()
                    if cmd:
                        print("Stopping run early")
                        break
            ret = np.array(self.measure(chs=chns))
            timegroup.append(ret[:,0,:][None])
            wfmgroup.append(ret[:,1,:][None])
            if i%updateN == 0:
                print('{0} events acquired...'.format(i))
        h5file.close()
        print("Saved {0} events to disk.".format(i+2))
        return

def testscript():
    d=PyDRS()
    d.set_freq(5.0)
    d.set_input_range(0)
    #d.set_trigger(ch=0,delay=50)
    d.set_trigger_proper()
    chans = [1,2,3,4]
    dat=d.measure(chs=chans)
    return d, dat, chans

def makeplot(data):
    '''
    Take ctype array of (chans, [time, voltage], data) and make a plot.
    '''
    nchans = len(data)
    fig = plt.figure()
    for i in range(nchans):
        plt.plot(np.array(data[i][0]), np.array(data[i][1]), label='ch{0}'.format(i+1))

    plt.legend()
    return

def plotevent(h5file, evtnum, chs = [1,2,3,4], fig=None):
    '''
    Plot a given event from the HDF5 file.
    '''
    h5file = tables.openFile(h5file, 'r')
    if fig is None:
        fig = plt.figure()
    wfm = h5file.root.wfms[evtnum]
    t = h5file.root.time[evtnum]
    for ch in chs:
        plt.plot(t[ch-1], wfm[ch-1], label='ch{0}'.format(ch))
    plt.legend()
    h5file.close()
    return fig

if __name__=="__main__":
    d, dat, chans = testscript()
    #thepanel = pd.Panel(np.array(dat), items=['ch{0}'.format(ch) for ch in chans],
    #                    major_axis=['time', 'voltage'])
    #thepanel.to_hdf('testdata.h5', '/waveforms/{0}'.format(time.time()), mode='a')#, format='table', append=True)

