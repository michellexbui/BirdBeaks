#!/usr/bin/env python
'''
A package for interpolating magnetometer data to explore the effects of field changes on
migrating bird behavior and adaptations.
'''

# Import everything first!
import numpy as np
from datetime import datetime as dt
import pickle
import matplotlib.pyplot as plt
import datetime
import supermag

def make_Dict(file_name):
    '''
    Make supermagfile, which takes the pickle Dr. Welling created and appends station information
    '''

    #load the pickle information
    supermagfile = pickle.load(open(file_name,'rb'))

    #load station info
    info = supermag.read_statinfo()
    for s in supermagfile:
        if s in info:
            supermagfile[s]['geolon'] = info[s]['geolon']
            supermagfile[s]['geolat'] = info[s]['geolat']
            supermagfile[s]['name']   = info[s]['station-name']

    return supermagfile

def interp_file(supermagfile, lon, lat, leap=True):
    '''
    Load a ascii-formatted SuperMag file and convert it to a
    Python pickle for fast loading later.
    '''

    from scipy.interpolate import NearestNDInterpolator

    import BirdBeaks

    # CHANGE ME:
    name_radar = 'KLNX'

    magarray = BirdBeaks.MagArray(supermagfile)

    #bird station we are testing
    birdstation = {}
    birdstation['time'] = []
    birdstation['b'] = []

    #account for leap year?
    if leap == True:
        for i in range(8784):
            birdstation['time'].append(supermagfile['time'][i*60])
    if leap == False:
        for i in range(8760):
            birdstation['time'].append(supermagfile['time'][i*60])

    #create file
    f = open(f'2008_{name_radar}.txt','w')
    f.write('2008 {} at longitude = {} and latitude = {}\n'.format(name_radar, lon, lat))

    #interpolate at each time.  Time this process.
    tStart = dt.now()
    for i in range(len(birdstation['time'])):
        b = magarray(birdstation['time'][i], lon, lat)
        birdstation['b'].append(b)

        # #masked array
        # birdmask = np.ma.masked_invalid(birdstation['b'])
        # maskedcount = len(birdmask) - birdmask.count()

        # #let us know, how many data values are masked
        # #print('birdmask has ', maskedcount, 'masked values')

        # #get the masked array
        # masks = np.ma.getmaskarray(birdmask)
        # for i in range(len(masks)):
        #     if masks[i]==True: #isolate the masked values and re-interpolate
        #         pass
        #     else: #if unmasked, just skip (:
        #         pass

        #print each interpolation
        #print('On {}, |B| at lon={}, lat={} is {:.3f} nT'.format(birdstation['time'][i], lon, lat, birdstation['b'][i]))
        #write into the file
        f.write('{} \t{} \n'.format(birdstation['time'][i], birdstation['b'][i]))
    f.close()

    # Calculate timing:
    nMins = (dt.now() - tStart).total_seconds()/60.

    #done message
    print(f'Finished with radar station {name_radar}')
    print(f'Process took {nMins}')

    return supermagfile, birdstation

def plot_b(supermagfile, birdstation):
    '''
    Plot each magnetometer station + the interpolated file, already done.
    '''
    #plot each of the three stations
    fig, axs = plt.subplots(3)
    fig.suptitle('Three Stations')
    axs[0].plot(supermagfile['time'],supermagfile['BOU']['b'])
    axs[0].set_ylabel('BOU b')
    #axs[1].plot(supermagfile['time'],supermagfile['M04']['b'])
    #axs[1].set_ylabel('M04 b')
    axs[1].plot(supermagfile['time'],supermagfile['T21']['b'])
    axs[1].set_ylabel('T21 b')
    axs[2].plot(birdstation['time'],birdstation['b'])
    axs[2].set_ylabel('interpolated')
    plt.show()

    return fig

if __name__ == "__main__":
    '''
    Run a quick test suite.
    '''
    supermagfile = make_Dict('test_mags.pkl')
    supermagfile, birdstation = interp_file(supermagfile, 260, 42)
    plot_b(supermagfile, birdstation)
