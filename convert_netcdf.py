#!/usr/bin/env python

'''
This script extracts information from a SuperMag NetCDF file and converts it
to a useable pickle.  It's a very rough draft of a script that should be
updated and adapted as we move forward.

Critical things to change: 
    - List of desired stations from static to any within lat/lon range
    - Input/output files as arguments
'''
from pickle import dump
from datetime import datetime as dt

import numpy as np
from scipy.io import netcdf_file

# These are the stations we want:
desired_stats = ['BOU', 'M04', 'T21']

# Open file:
f = netcdf_file('/home/dwelling/all_stations_all2008.netcdf')

# Get some basic info: size, etc.
nTime = f.variables['time_sc'].data.shape[0]

# Build map between station names and array location.
stat_names = {}
nStats = f.variables['id'].data.shape[1]
for i in range(nStats):
    stat_now = f.variables['id'].data[0,i,:]
    stat_names[''.join(stat_now.astype('str'))] = i

# Identify stations we want AND have that go into final output object.
stats = []
for s in desired_stats:
    if s in stat_names: stats.append(s)

# Create basic data container:
data = {}
data['time'] = np.zeros(nTime, dtype=object)

# Build time array. This is going to be ugly.
for i in range(data['time'].size):
    data['time'][i] = dt(int(f.variables['time_yr'].data[i]),
                         int(f.variables['time_mo'].data[i]),
                         int(f.variables['time_dy'].data[i]),
                         int(f.variables['time_hr'].data[i]),
                         int(f.variables['time_mt'].data[i]),
                         int(f.variables['time_sc'].data[i]))

# Populate station data:
for s in stats:
    # Grab magnetometer data:
    data[s] = {'bx':f.variables['dbn_nez'].data[:,stat_names[s]],
               'by':f.variables['dbe_nez'].data[:,stat_names[s]],
               'bz':f.variables['dbz_nez'].data[:,stat_names[s]]}
    # Calculate magnitude of the field perturbation:
    data[s]['b'] = np.sqrt(data[s]['bx']**2+data[s]['by']**2+data[s]['bz']**2)

f.close()

# Save results as a pickle:
with open('test_mags.pkl', 'wb') as out:
    dump(data, out)