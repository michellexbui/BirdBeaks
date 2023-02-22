#!/usr/bin/env python3

'''
This script extracts information from a SuperMag NetCDF file and converts it
to a useable pickle.  It's a very rough draft of a script that should be
updated and adapted as we move forward.

Beyond saving the three-component field for each desired station and the
corresponding time, the magnitude of $\Delta B$ is calculated. Further, a
rolling maximum of the field magnitude is generated using a window of size
`windowsize` (see argument list below) centered about each epoch. For example,
if the default window size of 61 is used, and the data is minute-sampled,
the rolling max for some time, t, will be the maximum value from
t-30mins to t+30mins.

Usage example: convert_netcdf.py all_stations_all1970.netcdf

Critical things to change:
    - List of desired stations from static to any within lat/lon range
    - Input/output files as arguments
'''
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from pickle import dump
from datetime import datetime as dt

import numpy as np
from scipy.io import netcdf_file

import supermag
from BirdBeaks import std_mags as desired_stats

# Start by setting up args.
parser = ArgumentParser(description=__doc__,
                        formatter_class=RawDescriptionHelpFormatter)
parser.add_argument("mags", type=str, metavar='supermag_file',
                    help="Path of SuperMag observations NetCDF file.")
parser.add_argument("-ws", "--windowsize", type=int, default=61,
                    help="Set size of window for rolling maximum |B|. " +
                         "Must be an odd number.")
args = parser.parse_args()

# Get all station info:
info = supermag.read_statinfo()

# Open file:
f = netcdf_file(args.mags)

# Get some basic info: size, etc.
nTime = f.variables['time_sc'].data.shape[0]
width = int(np.floor(args.windowsize/2))

# Build map between station names and array location.
stat_names = {}
nStats = f.variables['id'].data.shape[1]
for i in range(nStats):
    stat_now = f.variables['id'].data[0, i, :]
    stat_names[''.join(stat_now.astype('str'))] = i

# Identify stations we want AND have that go into final output object.
stats = []
for s in desired_stats:
    if s in stat_names:
        stats.append(s)

# Print out some info:
print("Input file information:")
print(f"\tNumber of mags: {nStats}")
print(f"\tNumber of desired mags: {len(stats)}/{len(desired_stats)}")

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
    data[s] = {'bx': f.variables['dbn_nez'].data[:, stat_names[s]],
               'by': f.variables['dbe_nez'].data[:, stat_names[s]],
               'bz': f.variables['dbz_nez'].data[:, stat_names[s]]}

    # Calculate magnitude of the field perturbation:
    data[s]['b'] = np.sqrt(data[s]['bx']**2+data[s]['by']**2+data[s]['bz']**2)

    # Calculate rolling maximum of b:
    nPoints = data[s]['b'].size
    data[s]['bmax'] = np.zeros(nPoints)
    for i in range(nPoints):
        istart, istop = max(0, i-width), min(i+width, nPoints)
        vals = data[s]['b'][istart:istop]
        if vals[np.isfinite(vals)].size:
            data[s]['bmax'][i] = vals[np.isfinite(vals)].max()
        else:
            data[s]['bmax'][i] = np.nan

    # Add information:
    if s in info:
        data[s]['geolon'] = info[s]['geolon']
        data[s]['geolat'] = info[s]['geolat']
        data[s]['name'] = info[s]['station-name']
    else:
        data[s]['geolon'] = -1
        data[s]['geolat'] = -1
        data[s]['name'] = '   '

# Create an output file name:
outfile = f'magdata_{data["time"][0]:%Y}.pkl'
# Save results as a pickle:
with open(outfile, 'wb') as out:
    dump(data, out)

# Close the stupid netcdf file
# f.close()
