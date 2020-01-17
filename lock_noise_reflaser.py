# -*- coding: utf-8 -*-
"""
Created on Fri Jun 29 15:35:42 2018

@author: Klaus
Countermessungen mit Pendulum
Abgeschreiben von lock_noise.py
"""

from time import sleep


from cnt90 import CNT90
#import rpyc
import json
import numpy as np
from matplotlib import pyplot as plt
from scipy import signal
import allantools
import datetime

plt.rcParams['figure.facecolor'] = 'lightgrey'

def append_number_to_filename(filename):
    """
    Adds a number suffix to a filename.
    """
    parts = filename
#    [*parts, ending] = filename.split('.')
    counter = 0
    
    while True:
#        test_filename = '.'.join(parts + ['%d' % counter] + [ending])
        test_filename = parts + '_%d' % counter
        try:
            open(test_filename + '.json', 'r')
        except FileNotFoundError:
            return test_filename
        
        counter += 1
        
        if counter > 1000:
            raise Exception('ffoop0')
            

def freqmeas(MEASUREMENT_TIME = 1, NO_OF_SAMPLES= 100000, COUNTER = 'C'):#,MEASUREMENT_RATE= 10**5):
#    MEASUREMENT_TIME = 1
    MEASUREMENT_RATE = int(NO_OF_SAMPLES/MEASUREMENT_TIME)
    print(MEASUREMENT_RATE)
    print(MEASUREMENT_TIME)
#    IS_LOCKED = False
#    DATA_FOLDER = '../../../data/MAIUS-B/reflaser/K/'
#    DATA_NAME = 'Test_K_Q2_vs_MAIUS'
    DATIME = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    
    # counter = connect_to_device_service('192.168.1.176', 'cnt90')
#    counter = connect_to_device_service('USB0::0x14EB::0x0090::991234::INSTR', 'cnt90')
    # frequency_measurement = rpyc.async(counter.root.frequency_measurement)
    counter = CNT90('USB0::0x14EB::0x0091::956628::INSTR') # 'USB0::0x14EB::0x0090::991234::INSTR'

    print('starting measurement, t=', MEASUREMENT_TIME, 'sample rate', MEASUREMENT_RATE)
    result = counter.frequency_measurement(COUNTER.upper(), MEASUREMENT_TIME, MEASUREMENT_RATE)
    data = result
    print(len(result))
    
    # data = list(result.value)
    
    data_res = data - np.mean(data)
    
    file_name_2 = '_%s_%ds' % ('locked' if IS_LOCKED else 'free', MEASUREMENT_TIME)
    
    data_file_name = append_number_to_filename(
            DATA_NAME + file_name_2+'_freqnoise'
            )
    
    f = open(data_file_name + '.json', 'x')
#    f = open(data_file_name[:-16]+data_file_name[-6:-4]+'.json', 'w')
#    f = open(DATA_FOLDER + DATA_NAME+'_' +str(iternum)+'_%s_%ds.json' % ('locked' if IS_LOCKED else 'free', MEASUREMENT_TIME), 'w')
#    f = open('testing_%s_%ds.json' % ('locked' if IS_LOCKED else 'free', MEASUREMENT_TIME), 'w')
    json.dump({
        'measurement_time': MEASUREMENT_TIME,
        'measurement_rate': MEASUREMENT_RATE,
        'frequencies': data,
        'was_locked': IS_LOCKED
    }, f)
    f.close()
    
    TIME = np.linspace(0,MEASUREMENT_TIME,num=NO_OF_SAMPLES)
    
    plt.figure(figsize = (8,5))
    plt.plot(TIME, data_res, label = 'Mean frequency: %.1f +/- %.1f' % (np.mean(data)*1e-6, np.std(data)*1e-6 ))
    plt.ylabel('Frequency / Hz')
    plt.xlabel('TIME / s')
    plt.legend()
    plt.grid(True, which = 'both', ls = '-')
    
    plt.savefig(data_file_name + '_timerec.pdf',
#    plt.savefig(data_file_name[:-16]+ '-timerec'+data_file_name[-6:-4]+'.png',
#    plt.savefig(data_file_name_2.replace('.json', 'timerec.png'),
#    plt.savefig(DATA_FOLDER + DATA_NAME+'_' +str(iternum) +'-timerec.png',
                #This is simple recomendation for publication plots
                dpi=300,
                # Plot will be occupy a maximum of available space
                bbox_inches='tight',
                )
    plt.show()
    
    fs = MEASUREMENT_RATE 
    
    f, Pxx_spec = signal.welch(data, fs, ('kaiser', 100), nperseg=1024, scaling='density')
    plt.figure(figsize = (8,5))
    plt.loglog(f, np.sqrt(Pxx_spec))
    plt.xlabel('Frequency / Hz')
    plt.ylabel('Frequency noise ASD  / $Hz/\sqrt{Hz}$')
    plt.grid(True, which = 'both', ls = '-')
    plt.savefig(data_file_name + '.pdf',
#    plt.savefig(data_file_name,
#    plt.savefig(data_file_name_2.replace('.json', '-freqnoise.png'),
#    plt.savefig(DATA_FOLDER +  DATA_NAME +'_' +str(iternum) +'-freqnoise.png',
                 #This is simple recomendation for publication plots
                dpi=300,
                # Plot will be occupy a maximum of available space
                bbox_inches='tight',
                )
    plt.show()
    
    data_rel = np.array(data)*767e-9/2.99e8
    # calculate the Allan deviation
    tau_max = np.log10(len(data)) # 
    taus = np.logspace(0,tau_max)/fs
    (taus_used, adev, adeverror, adev_n) = allantools.adev(data_rel, data_type='freq', rate=fs, taus=taus)
        
    plt.figure(figsize = (8,5))
    # plot the Allan devation
    plt.subplot(111, xscale = 'log', yscale = 'log')
    plt.errorbar(taus_used, adev, yerr=adeverror)
    plt.xlabel('Averaging time t (s)')
    plt.ylabel('Allan deviation $\sigma_y(t)$')
    #plt.legend(fontsize = 'xx-small') # too many legend entries...
    plt.grid(b='on', which = 'minor', axis = 'both')
    plt.box(on='on')
    plt.savefig(data_file_name + '_allan.pdf',
#    plt.savefig(data_file_name[:-16]+ '-Allan'+data_file_name[-6:-4]+'.png',
#    plt.savefig(data_file_name_2.replace('.json', '-Allan.png'),
#    plt.savefig(DATA_FOLDER + DATIME +  DATA_NAME +'-Allan.png',
#    plt.savefig(DATA_FOLDER+  DATA_NAME+'_' +str(iternum) +'-Allan.png',
                #This is simple recomendation for publication plots
                dpi=300,
                # Plot will be occupy a maximum of available space
                bbox_inches='tight',
                )
    plt.show()
    
# Measurement loop    
IS_LOCKED = False
DATA_FOLDER = '/home/qom/GAIN'
DATA_NAME = 'Testing'
NO_OF_SAMPLES = 10**5 ## MAXIMUM = 10^5
COUNTER = 'A'

for t in [1, 10, 100]:
    freqmeas(t)#Default no. of samples = 10**5, Default counter = 'C'
#    freqmeas(MEASUREMENT_TIME = t)#,MEASUREMENT_RATE = 10**5)
#
