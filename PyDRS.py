import ctypes, json, time, datetime, sys, os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import tables, sense_hat
from multiprocessing import Process, Pipe

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
                      'TrigSource_OR': [False,True,False,False],
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
        time.sleep(0.001)
        self.set_input_range(self.paramdict['RangeCentre_V'])
        time.sleep(0.001)
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
        else:
            print('set drs_setInputRange')
        return
        
    def set_freq(self,freq):
        '''
        Set the domino sampling frequency (GHz)
        '''
        if not so.drs_setFrequency(self.drs,
                ctypes.c_double(freq),True):
            print('drs_setFrequency not set!')
        else:
            print('set drs_setFrequency')
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
                        print("set drs_enableTrigger")
                else:
                    #Transparent mode is needed for analog trig
                    time.sleep(0.001)
                    if not so.drs_setTranspMode(self.drs, 1):
                        print('drs_setTranspMode not set!')
                    else:
                        print('set drs_setTranspMode')
                    time.sleep(0.001)
                    if not so.drs_enableTrigger(self.drs,1,1):
                        ##lemo off, analog trigger on
                        print('drs_enableTrigger not set!')
                    else:
                        print("set drs_enableTrigger")
                    time.sleep(0.001)
                    tmask = self._calc_trig_mask()
                    if tmask == 0:
                        print("TRIGGER NOT SET!")
                        return
                    if not so.drs_setTriggerSource(self.drs, 
                            ctypes.c_ushort(tmask)):
                        print('drs_setTriggerSource not set!')
                    else:
                        print('set drs_setTriggerSource')
                    time.sleep(0.001)
                    for ch, lvl in enumerate(self.paramdict['TrigLevels_V']):
                        time.sleep(0.001)
                        if so.drs_setIndividualTriggerLevel(self.drs, ch, ctypes.c_double(lvl)) < 0:
                            print('drs_setIndividualTriggerLevel\
                                    not set!')
                        else:
                            print('set drs_setIndividualTriggerLevel for ch{0}'.format(ch))

                    time.sleep(0.001)
                    if not so.drs_setTriggerPolarity(self.drs,
                            self.paramdict['isNegTrigPolarity']):
                        print('drs_setTriggerPolarity not set!')
                    else:
                        print('set drs_setTriggerPolarity')
                    time.sleep(0.001)
                    if not so.drs_setTriggerDelayNs(self.drs,
                            self.paramdict['TrigDelay_ns']):
                        print('drs_setTriggerDelayNs not set')
                    else:
                        print('set drs_setTriggerDelayNs')
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
        
    def measure(self,chs=[1],timeout=10000, softtrig=False, verbose=False):
        so.drs_startDomino(self.drs)
        if not softtrig:
            i=0
            #print("waiting for trigger...")
            while i< timeout:
                if so.drs_isBusy(self.drs)==0:
                    break
                time.sleep(0.001)
                i+=1
                if i%1000 == 0 and verbose:
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

    def _run_vibcal(self, therow, shat, vthresh, nBG):
        '''
        Run the vibration calibration and write to file.
        returns mean and sigmas for vibration baselines.
        '''
        #Take background vibration samples (this assumes there is no vibration during the BG meas).
        x_BG = np.empty(nBG, dtype=np.float32)
        y_BG = np.empty(nBG, dtype=np.float32)
        z_BG = np.empty(nBG, dtype=np.float32)
        calstart = time.time()
        for i in range(nBG):
            x_BG[i] = shat.get_accelerometer_raw()['x']
            y_BG[i] = shat.get_accelerometer_raw()['y']
            z_BG[i] = shat.get_accelerometer_raw()['z']
        
        therow['vibr_threshold'] = vthresh
        therow['vibr_BL_x'] = x_BG.mean()
        therow['Uvibr_BL_x'] = x_BG.std()
        therow['vibr_BL_y'] = y_BG.mean()
        therow['Uvibr_BL_y'] = y_BG.std()
        therow['vibr_BL_z'] = z_BG.mean()
        therow['Uvibr_BL_z'] = z_BG.std()
        therow['T_unit'] = 'C'
        therow['P_unit'] = 'mbar'
        therow['H_unit'] = '%'
        therow['vibx_raw'] = x_BG
        therow['viby_raw'] = y_BG
        therow['vibz_raw'] = z_BG
        therow['calstart'] = calstart
        calend = time.time()
        therow['calend'] = calend
        therow.append()
        return x_BG.mean(), y_BG.mean(), z_BG.mean(), \
                x_BG.std(), y_BG.std(), z_BG.std()


    def _meas_env(self, fname, mypipe, vthresh = 3, nBG=500):
        '''
        NOTE: SPAWNED AS A SUBPROCESS BY run_and_save (if meas==True).
        Begin acquiring data with the sense hat sensor board, storing in fname.
        File structure:
           root/
               TPH (table) <-- timestamp, temp, pressure, humidity, sampled every second.
               vibrate (table) <-- timestamp, vibration x/y/z, when above trigger
               rundata (table) <-- vibration trigger threshold, vibraiton baselines, units.

        vthresh is the trigger threshold for detecting a vibration, in units of normalised sigma.

        nBG is the number of points to acquire for estimating the vibrations.
        '''
        envfile = tables.openFile(fname, mode='a')
        shat = sense_hat.SenseHat()
        #collect and write rundata:
        class rundata(tables.IsDescription):
            vibr_threshold = tables.Float32Col()
            vibr_BL_x = tables.Float32Col()
            vibr_BL_y = tables.Float32Col()
            vibr_BL_z = tables.Float32Col()
            Uvibr_BL_x = tables.Float32Col()
            Uvibr_BL_y = tables.Float32Col()
            Uvibr_BL_z = tables.Float32Col()
            T_unit = tables.StringCol(8) #8-char string
            P_unit = tables.StringCol(8)
            H_unit = tables.StringCol(8)
            vibx_raw = tables.Float64Col(shape=(nBG,))
            viby_raw = tables.Float64Col(shape=(nBG,))
            vibz_raw = tables.Float64Col(shape=(nBG,))
            calstart = tables.Float64Col()
            calend = tables.Float64Col()

        rdtable = envfile.create_table(envfile.root, 'rundata',
                                       rundata, 'Run Data')
        therow = rdtable.row
        xmean, ymean, zmean, xstd, ystd, zstd = \
                self._run_vibcal(therow, shat, vthresh, nBG)

        rdtable.flush()

        #Initialise TPH and EArray:
        class TPH(tables.IsDescription):
            T = tables.Float64Col()
            P = tables.Float64Col()
            H = tables.Float64Col()
            unixtime = tables.Float64Col()

        class vibrate(tables.IsDescription):
            x = tables.Float64Col()
            y = tables.Float64Col()
            z = tables.Float64Col()
            unixtime = tables.Float64Col()

        TPHtab = envfile.create_table(envfile.root, 'TPH', TPH, 
                                      'Temperature, Pressure, Humidity')
        TPHrow = TPHtab.row
        vibtab = envfile.create_table(envfile.root, 'vibrate', vibrate, 
                                      'Triggered Vibrations')
        vibrow = vibtab.row

        #Spawn vibration search process; with a pipe connecting to this one:
        #Note, this proc CANNOT write to file!
        parentmsg, childmsg = Pipe()
        vibproc = Process(target=self._MeasureVibes, 
                    args=(childmsg, vthresh, xmean, ymean, zmean,
                          xstd, ystd, zstd))
        
        #Get the median temperature at which the calibration was done:
        #(This is so we can re-do the vibration calibration with temp change).
        ntemp = 10
        thetemps = np.empty(ntemp, dtype=np.float64)
        for i in range(10):
            thetemps[i] = shat.get_temperature()
        caltemp = np.median(thetemps)
        maxtempdiff = 2 #max deviation from calib temp allowed.
                    
        #Collect TPH until stop_env is called.
        stopflag = False
        loopctr = 0
        
        #Let the parent know that the initialisation is done.
        mypipe.send(True)
        vibproc.start()
        maxvibread = 100
        while not stopflag:
            #now collect TPH and check if there's a vibration trigger.
            thistemp = shat.get_temperature()
            TPHrow['T'] = thistemp
            thetemps[loopctr%ntemp] = thistemp
            TPHrow['unixtime'] = time.time()
            TPHrow['P'] = shat.get_pressure()
            TPHrow['H'] = shat.get_humidity()
            TPHrow.append()
            TPHtab.flush()
            vibreads = 0
            while parentmsg.poll() and vibreads<maxvibread:
                #save the vibration trigger.
                vibrow['unixtime'], vibrow['x'], vibrow['y'], vibrow['z'] = \
                        parentmsg.recv()
                vibrow.append()
                vibreads += 1
            if vibreads:
                vibtab.flush()
                vibreads = 0
            if mypipe.poll():
                stopflag = mypipe.recv()
                if stopflag:
                    parentmsg.send(True)
                    TPHtab.flush()
                    vibtab.flush()
                    envfile.close()
            #sleep until next measurement
            time.sleep(1)
            loopctr += 1
            if np.abs(np.median(thetemps)-caltemp)>maxtempdiff:
                vibproc.terminate()
                #Redo the vibration calibration for the new temperature.
                xmean, ymean, zmean, xstd, ystd, zstd = \
                    self._run_vibcal(therow, shat, vthresh, nBG)
                rdtable.flush()
                vibproc = Process(target=self._MeasureVibes, 
                            args=(childmsg, vthresh, xmean, ymean, zmean,
                                  xstd, ystd, zstd))
                vibproc.start()
                for i in range(10):
                    thetemps[i] = shat.get_temperature()
                caltemp = np.median(thetemps)
                

        #double check the subp is dead
        if vibproc.is_alive():
            vibproc.terminate()
        
        envfile.close()
        return

    def _MeasureVibes(self, mypipe, thresh, x_BG, y_BG, z_BG,
                      Ux_BG, Uy_BG, Uz_BG):
        '''
        NOTE: THIS MUST BE CALLED AS A SUBPROCESS BY meas_env!
        Search for triggered vibrations and communicate when there is one.
        Stops when passed a message by the parent process.
        From testing: there's no issue with simultaneous reads from the sense hat.
        '''
        shat = sense_hat.SenseHat()
        stopflag = False

        while not stopflag:
            if mypipe.poll():
                stopflag = mypipe.recv()
            accel = shat.get_accelerometer_raw()
            this_x = accel['x']
            this_y = accel['y']
            this_z = accel['z']
            if (np.abs(x_BG - this_x)>thresh*Ux_BG) or \
               (np.abs(y_BG - this_y)>thresh*Uy_BG) or \
               (np.abs(z_BG - this_z)>thresh*Uz_BG):
                   thetime = time.time()
                   mypipe.send([thetime, this_x, this_y, this_z])
        return

    def run_and_save(self, nevents, fname, chns=[1,2,3,4], updateN=10000, mypipe=None,
                     sensor=True, softtrig=False):
        '''
        Acquire nevents waveforms and store in fname as HDF5 file.
        '''
        if sensor:
            parentmsg, childmsg = Pipe()
            #Write env data to separate file to avoid concurrent writing.
            envfname = fname.replace('.h5', '_env.h5')
            envproc = Process(target=self._meas_env, args=(envfname, childmsg))
        retarr = np.array([])
        #Acquire 1 sample to test.
        ret = np.array(self.measure(chs=chns, softtrig=softtrig))
        tnow = np.array(time.time())
        h5file = tables.openFile(fname, mode='a')
        chndepth = so.drs_getChannelDepth(self.drs)
        #lzo is a good tradeoff btw compression and speed.
        compfilter = tables.Filters(complevel=1, complib='lzo')
        tstampgroup = h5file.createEArray(h5file.root, 'unixtime',
                tables.Atom.from_dtype(tnow.dtype), shape=(0,), filters=compfilter)
        timegroup = h5file.createEArray(h5file.root, 'time',
                tables.Atom.from_dtype(ret[:,0,:].dtype),
                shape=(0, ret[:,0,:].shape[0], ret[:,0,:].shape[1]),
                filters=compfilter, expectedrows=chndepth)
        wfmgroup = h5file.createEArray(h5file.root, 'wfms',
                tables.Atom.from_dtype(ret[:,1,:].dtype),
                shape=(0, ret[:,1,:].shape[0], ret[:,1,:].shape[1]),
                filters=compfilter, expectedrows=chndepth)
        metaarr = h5file.create_array(h5file.root, "run_info", [self.comments, json.dumps(self.paramdict)], 'run_info')
        tstampgroup.append(tnow[None])
        timegroup.append(ret[:,0,:][None])
        wfmgroup.append(ret[:,1,:][None])
        envproc.start()
        print("Initializing sense hat: make sure you stay very still...")
        while True:
            if parentmsg.poll():
                break #this only sends a message when it's done initialising.
        print("Done. Taking data now")
        if nevents<0:
            nevents = sys.maxint
        for i in range(nevents-1):
            ret = np.array(self.measure(chs=chns, softtrig=softtrig))
            tstampgroup.append(np.array(time.time())[None])
            timegroup.append(ret[:,0,:][None])
            wfmgroup.append(ret[:,1,:][None])
            if i%updateN == 0:
                print('{0} events acquired...'.format(i))
            if not mypipe is None:
                if mypipe.poll():
                    cmd = mypipe.recv()
                    if cmd:
                        print("Stopping run early")
                        parentmsg.send(True)
                        break
        h5file.close()
        print("Saved {0} events to disk.".format(i+2))
        #double check the subp is dead
        time.sleep(5)
        if envproc.is_alive():
            envproc.terminate()
        
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

