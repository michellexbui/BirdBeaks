#!/usr/bin/env python
'''
A package for interpolating magnetometer data to explore the effects of field changes on 
migrating bird behavior and adaptations.
'''

# Import everything first!
import supermag
import numpy as np
from datetime import datetime as dt

def ascii_to_pickle(supermag_file):
    '''
    Load a ascii-formatted SuperMag file and convert it to a 
    Python pickle for fast loading later.
    '''
    import pickle

    # Load ascii data.
    raw = supermag.SuperMag(supermag_file, load_info=True)
    raw.calc_btotal()

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

    The object is arranged thusly:

    self.data -- A supermag.SuperMag object that stores the raw data from
                 which we interpolate in time and space.
    self.points -- An array of shape [nMag, 2] containing the lons and lats
                   of each magnetometer in self.data.
    
    Example
    -------
    # Create a MagArray object from data in repository:
    >>> import BirdBeaks
    >>> a = BirdBeaks.MagArray('BirdBeaks/data/supermag_example.txt')
    
    # Explore contents of file:
    >>> print(a.data.keys())
    >>> print(a.data['BOU']['bx'])
    >>> print(a.points.shape)
    >>> print( len(a.data.keys()) )

    '''
    
    #Defining the input: longitude, latitude, and string date in the form of 'YYYY/MM/DD/hh/mm'
    def __init__(self, filename): #igeolon, igeolat, istrdt):
        import pickle
        
        # Open the data file, store in a SuperMag object.
        # If it's a pickle, unpickle it.  Otherwise, open the ASCII object.
#        if filename[-4:] == '.txt': # We have an ASCII file:
#            self.data = supermag.SuperMag(filename, load_info=True)
#            self.data.calc_btotal()
#        elif filename[-4:] == '.pkl': # We have a pickle!
#            raw = open(filename, 'rb')
#            self.data = pickle.load(raw)
#        else:
#            raise ValueError("Unknown file format for {}".format(filename))
        self.data = filename

        # Create dictionary to hold interpolator objects:
        self.interp = {}

        # Store list of stations:
        mags = list(self.data.keys())
        mags.remove('time')
        nummags = len(mags)
        
        # For each station, save the lon/lat:
        self.points = np.zeros( [len(self.data)-1, 2] )
        for i, m in enumerate(mags):
            self.points[i,:] = (self.data[m]['geolon'], self.data[m]['geolat'])
        
    def __call__(self, time, lon, lat):
        '''
        For a specific time (scalar), return $\Delta B$ at 
        an arbitrary latitude and longitude.  
        '''

        # Check to make sure time does not exceed boundaries of
        # loaded magnetometer data:
        if time > self.data['time'][-1] or time<self.data['time'][0]:
            print(f'Time requested = {time}')
            print(f"Data time ranges from {self.data['time'][0]} to {self.data['time'][0]}")
            raise ValueError('Time outside of data bounds!')

        # POTENTIAL THING HERE: REDUCE DATETIME TO MINUTE RESOLUTION?
        
        # Find interpolator that matches this time.  If it doesn't exist, 
        # make it and save it!
        if time not in self.interp:
            self._create_interp(time)
        
        product = self.interp[time](lon, lat)
        
        # mags = list(self.data.keys())
        # mags.remove('time')
        # nummags = len(mags)

        #check if nan or number
        #import math
        if np.isnan(product):
            raise ValueError('NaN detected in output')
        #if checkifnan == True:
        #    for a in range(nummags):
        #        self._create_reinterp(time, a)
        #        product = self.interp[time](lon, lat)
        #        checknan = math.isnan(product)
        #        if checknan == True:
        #            continue
        #        elif checknan == False:
        #            break
        #elif checkifnan == False:
        #    pass

        return product

    def __str__(self):
        '''
        Make printing work good.
        '''
        return 'MagArray spanning T={},{}; lons={},{}; lats={},{}'.format(
            self.data['time'][0], self.data['time'][-1],
            self.points[:,0].min(), self.points[:,0].max(),
            self.points[:,1].min(), self.points[:,1].max())
            
    
    def _create_interp(self, time):
        '''
        For a given time, set up an interpolation object.
        '''
        from scipy.interpolate import LinearNDInterpolator

        # Get position corresponding to current time.
        loc = self.data['time'] == time
                
        # Create empty arrays for lon/lat and b_total:
        b = np.zeros( len(self.data)-1 )
        
        # Get list of stations:
        mags = list(self.data.keys())
        mags.remove('time')
        
        # For each station, save the lon/lat and |b| for time zero:
        for i, m in enumerate(mags):
            b[i] = self.data[m]['b'][loc]

        # Create filter to only keep real/finite values, remove nans.
        filter = np.isfinite(b)
        
        # Create our interpolator object:
        self.interp[time] = LinearNDInterpolator(
            self.points[filter,:], b[filter])
        
        # Test it!
        #print('|B| at lon={}, lat={} is {:.3f}nT'.format(
        #    lon, lat, self[time](lon, lat)))

    def _create_newinterp(self, time):
        '''
        For a given time, set up an interpolation object.
        '''
        from scipy.interpolate import NearestNDInterpolator

        # Get position corresponding to current time.
        loc = self.data['time'] == time
                
        # Create empty arrays for lon/lat and b_total:
        b      = np.zeros( len(self.data)-1 )
        
        # Get list of stations:
        mags = list(self.data.keys())
        mags.remove('time')
        
        # For each station, save the lon/lat and |b| for time zero:
        for i, m in enumerate(mags):
            b[i]        = self.data[m]['b'][loc]
            
        # Create our interpolator object:
        self.interp[time] = NearestNDInterpolator(self.points, b)
        
        # Test it!
        #print('|B| at lon={}, lat={} is {:.3f}nT'.format(
        #    lon, lat, self[time](lon, lat)))


    def _create_reinterp(self, time, a):
        '''
        For a given time, set up an interpolation object.
        '''
        from scipy.interpolate import LinearNDInterpolator

        # Get position corresponding to current time.
        loc = self.data['time'] == time
                
        # Create empty arrays for lon/lat and b_total:
        b      = np.zeros( len(self.data)-1 )
        
        # Get list of stations:
        mags = list(self.data.keys())
        mags.remove('time')
        mags.remove(mags[a])
        
        # For each station, save the lon/lat and |b| for time zero:
        for i, m in enumerate(mags):
            b[i]        = self.data[m]['b'][loc]
            
        # Create our interpolator object:
        self.interp[time] = LinearNDInterpolator(self.points, b)
        
        # Test it!
        #print('|B| at lon={}, lat={} is {:.3f}nT'.format(
        #    lon, lat, self[time](lon, lat)))

if __name__ == "__main__":
    '''
    Run a quick test suite.
    '''
    pass
