#!/usr/bin/env python
'''
A package for interpolating magnetometer data to explore the effects of field changes on 
migrating bird behavior and adaptations.
'''

# Import everything first!
import supermag
import numpy as np
from datetime import datetime as dt
from scipy.interpolate import LinearNDInterpolator

def ascii_to_pickle(supermag_file):
    '''
    Load a ascii-formatted SuperMag file and convert it to a 
    Python pickle for fast loading later.
    '''
    import pickle

    # Load ascii data.
    raw = supermag.SuperMag(supermag_file, load_info=True)

    # Get name for output file:
    outname = '.'.join(supermag_file.split('.')[:-1]) + '.pkl'

    # Open binary file, dump contents as a pickle:
    out = open(outname, 'wb')
    pickle.dump(raw, out)
    out.close()

    return True
    
#Method which takes in geographic longitude, geographic latitude, and a string date & yields |B|
class MagArray(object):
    '''
    Load a SuperMAG data file and use the included data to explore
    magnetic values at any arbitrary point.
    '''
    #Defining the input: longitude, latitude, and string date in the form of 'YYYY/MM/DD/hh/mm'
    def __init__(self, igeolon, igeolat, istrdt):
        self.igeolon = igeolon
        self.igeolat = igeolat
        self.istrdt  = istrdt

        #me making sure this inputes the right values, probably unnecessary
        print(igeolon)
        print(igeolat)
        print(istrdt)

        #Turning this string 'YYYY/MM/DD/hh/mm' into a datetime
        idt = dt.strptime(istrdt, '%Y/%m/%d/%H/%M')
        
        #me printing it for my own sake
        print(idt)

        # Open the data file, store in a SuperMag object:
        data = supermag.SuperMag('./supermag_northamer_2001.txt', load_info=True)
        
        # For each magnetometer in our file, calculate |b|:
        data.calc_btotal()

        #Match time in array to input datetime
        for n in range(0, len(data['time'])):
            if data['time'][n] == idt:
                fdt = data['time'][n]
                print(fdt)
                p = n #defining p to be n, the "slot" whose time matched the input time 
                print(p)
        
        # Create empty arrays for lon/lat and b_total:
        points = np.zeros( [len(data)-1, 2] )
        b      = np.zeros( len(data)-1 )

        # Get list of stations:
        mags = list(data.keys())
        mags.remove('time')

        # For each station, save the lon/lat and |b| for time zero:
        for i, m in enumerate(mags):
            points[i,:] = (data[m]['geolon'], data[m]['geolat'])
            b[i]        = data[m]['b'][p] # Get B at station m at time p as initiated above in line 39.

        #make pickle from here
        
        # Create our interpolator object:
        #also me wanting to see what values tri_int uses
        #print(points)
        #print(b)                      
        tri_int = LinearNDInterpolator(points, b)

        # Test it!
        print('|B| at lon={}, lat={} is {:.3f}nT'.format(igeolon, igeolat, tri_int(igeolon, igeolat)))        


if __name__ == "__main__":
    '''
    Run a quick test suite.
    '''
    pass
