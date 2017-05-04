import ctypes
import time,sys,os
import pandas as pd
import numpy as np
import tables
import datetime
import PyDRS
import json
from multiprocessing import Process, Pipe 

if __name__ == "__main__":
    print("This is a command line program to run the DRS4 DAQ\n")
    #Initialize the drs board.
    daq = PyDRS.PyDRS()
    parampath = '/home/pi/Downloads/drs-5.0.6/pydrs_thirono/PyDRS/params.json' 
    if os.path.isfile(parampath):
        print('Loading parameters from configuration file...')
        with open(parampath, 'r') as f:
            daq.paramdict = json.loads(f.readline())

    print("These are the current parameter settings:\n{0}\n".format(daq.paramdict))
    #TODO: make arbitrary parameters settable using UI.
    daq.set_params()
    exit = False
    par, child = Pipe()
    isrunning = False
    while not exit:
        print("To acquire N waveforms, just type the number. To exit, type e, to stop a run, type s")
        ret = raw_input()
        try:
            nevents = int(ret)
            if not isrunning:
                fname = 'run{0}.h5'.format(int(time.time()))
                print("Saving data to {0}".format(fname))
                daq.comments = raw_input("type some comments to include in the run file:\n")
                #TODO: let user choose which channels to run with.
                proc = Process(target=daq.run_and_save, 
                        args=(nevents, fname, [1,2,3,4], 1000, child))
                proc.start()
                #proc.join()
                isrunning = True
                #daq.run_and_save(nevents, fname)
            else:
                print("The data is already being acquired. Type 's' to stop.")
        except ValueError:
            if ret == 'e':
                break
            elif ret == 's':
                par.send(True)
                isrunning = False
            else:
                print('Input not understood! Try again...')
