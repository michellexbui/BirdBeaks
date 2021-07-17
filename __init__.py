#!/usr/bin/env python
'''
A package for interpolating magnetometer data to explore the effects of field changes on
migrating bird behavior and adaptations.
'''

# Import everything first!
import os
import supermag
import numpy as np
from datetime import datetime as dt

# Set install directory:
install_dir = '/'.join(__loader__.path.split('/')[:-1])+'/'

# Standard magnetometer set for NA interpolation:
std_mags = ['M01', 'M02', 'M03', 'M04', 'M05', 'M06', 'M07', 'M08', 'M09',
            'M10', 'M11', 'GLN', 'BOU', 'DLR', 'TUL', 'CDP', 'BSL', 'TUC',
            'BRD', 'TEO', 'BSL', 'PIN', 'C08', 'C11', 'C12', 'T18', 'T21',
            'T24', 'T56', 'T57', 'SJG', 'NEW', 'VIC', 'C10', 'DSO', 'T15',
            'OTT', 'CLK', 'PBQ', 'CRP', 'RAL', 'FRD', 'MSH', 'T17']

def load_radar_info():
    '''
    Read the radar location CSV file for use in generating radar location
    ground magnetic data.  Returns a dictionary with the following structure:

    info[radar_name] -> [geolat, geolon]

    ...where *radar_name* is the four letter radar code, latitude and longitude
    are in geographic coordinates.
    '''

    # Get file path:
    path = install_dir + '/data/radar_stations_ALL.csv'

    # Create container:
    info = {}

    # Read and parse data:
    with open(path, 'r') as f:
        # Skip header:
        f.readline()

        for l in f.readlines():
            parts = l.split(',')
            station = parts[0].replace('"','')
            info[station] = [float(parts[1]), float(parts[2])]
            if info[station][1]<=0: info[station][1]+=360.0
    return info

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

    def __call__(self, time, lon, lat, strict=False):
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
        if strict and np.isnan(product):
            raise ValueError('NaN detected in output')

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
        mags = np.array(mags, dtype=str)

        # For each station, save the lon/lat and |b| for time zero:
        for i, m in enumerate(mags):
            b[i] = self.data[m]['b'][loc]

        # Create filter to only keep real/finite values, remove nans.
        filter = np.isfinite(b)
        self.interp_mags = mags[filter]

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
        NOT USED.
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

def plot_station_map(show_names=True, mag_list=std_mags):
    '''
    Plot a map of magnetometer stations and radar stations.
    '''

    import matplotlib.pyplot as plt
    from matplotlib.image import imread
    from cartopy import crs

    # Get radar station info:
    radars = load_radar_info()

    # Load magnetometer info:
    mag_info = supermag.read_statinfo()

    # Set up plot of North America:
    #proj = crs.AlbersEqualArea(central_longitude=275,
    #                           standard_parallels=(25.0, 45.0))
    proj = crs.PlateCarree()

    fig = plt.figure(figsize=(10,8.13))
    ax = fig.add_subplot(111, projection=proj)

    # Add map to figure:
    fname = os.path.join(install_dir, 'data', 'NE1_50M_SR_W.tif')
    ax.imshow(imread(fname), origin='upper', transform=crs.PlateCarree(),
              extent=[-180, 180, -90, 90])

    # Add radar stations to figure:
    for r in radars:
        lat,lon=radars[r]
        ax.plot(lon, lat, 'ko', mfc='red', transform=proj)
        if show_names:
            ax.text(lon+.5, lat, r, ha='left', va='top', transform=proj, size=8)
    # Add magnetometers:
    for m in std_mags:
        if m in mag_list:
            mfc = 'blue'
        else:
            mfc = 'grey'
        lon, lat = mag_info[m]['geolon'], mag_info[m]['geolat']
        ax.plot(lon, lat, 'k^', mfc=mfc, transform=proj)
        if show_names:
            ax.text(lon-.5, lat, m, ha='right', va='top', transform=proj, size=8)

    # Customize axes:
    ax.set_extent([-125, -63, 9, 60])
    l1 = ax.plot(0,0, 'ko', mfc='red', transform=proj)
    l2 = ax.plot(0,0, 'k^', mfc='blue')
    l3 = ax.plot(0,0, 'k^', mfc='grey')
    ax.legend(l1+l2+l3, ['Radars', 'Magnetometers', 'Mags: No Data'],
              loc='upper left')
    fig.tight_layout()
    fig.tight_layout()

    return fig

if __name__ == "__main__":
    '''
    Run a quick test suite.
    '''
    pass
