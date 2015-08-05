import ctypes
import time,sys,os
sofile=os.path.join(os.path.dirname(os.path.realpath(__file__)),"libdrs.so")
so=ctypes.CDLL(sofile)
f1024=ctypes.c_float * 1024

class PyDRS:
    def __init__(self):
        self.drs=so.drs_create()
        n=so.drs_getNumberOfBoards(self.drs)
        if 1 !=n:
             "# of DRS board should be 1, %d"%n
             return

        print "Serial: %d"%so.drs_getBoardSerialNumber(self.drs),
        print "Firmware: %d"%so.drs_getFirmwareVersion(self.drs),
        print "Board type: %d"%so.drs_getBoardType(self.drs)
        so.drs_init(self.drs)
        so.drs_enableTcal(self.drs,1)  ### what does this function do? 
        
    def __del__(self):
       so.drs_delete(self.drs)
       
    def set_input_range(self,offset=0.0):
        so.drs_setInputRange(self.drs,ctypes.c_double(offset))  ## in V
        
    def set_freq(self,freq):
        so.drs_setFrequency(self.drs,freq,True)  ## freq in GHz max=5
        
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
            
        
    def measure(self,chs=[1],timeout=10000):
        so.drs_startDomino(self.drs)
        i=0
        while i< timeout:
            if so.drs_isBusy(self.drs)==0:
                break
            time.sleep(0.001)
        if i==timeout:
            print "measure() timeout!!"
        so.drs_transferWaves(self.drs,0,8)  ## TODO give optimal number
        ret=[]
        for i,ch in enumerate(chs):
            ret.append([f1024(),f1024()])
            tc=so.drs_getTriggerCell(self.drs,0)
            so.drs_getTime(self.drs,0, 2*(ch-1),tc,ret[i][0])
            so.drs_getWave(self.drs,0, 2*(ch-1), ret[i][1])
        return ret
        
if __name__=="__main__":
    d=PyDRS()
    d.set_freq(5.0)
    d.set_input_range(0)
    d.set_trigger(ch=1,delay=50)
    dat=d.measure(chs=[1,2])
    import numpy as np
    np.savetxt("data.txt",np.array(dat))
    
        


