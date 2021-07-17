#!/usr/bin/env python3

'''
This script uses the BirdBeak library to interpolate SuperMag data
to a set of radar locations.  To use, simply call while referencing
a python pickle of SuperMag data:

generate_db.py magdata_2008.pkl

A new folder will be created with the resulting data sets.

This script generalizes work performed by Michelle Bui, 2020.
'''

from argparse import RawDescriptionHelpFormatter, ArgumentParser

# Start by setting up args.
parser = ArgumentParser(description=__doc__,
                        formatter_class=RawDescriptionHelpFormatter)

parser.add_argument("mags", type=str,
                    help="Path of SuperMag observations python pickle.")
args = parser.parse_args()

# Continue imports now that args are handled:
import os
import pickle
import datetime as dt

import numpy as np
import matplotlib.pyplot as plt

import supermag
import BirdBeaks

# Load observed mag data, convert to BirdBeak object:
with open(args.mags, 'rb') as f:
    rawobs = pickle.load(f)
obs = BirdBeaks.MagArray(rawobs)

# Load radar station info:
radars = BirdBeaks.load_radar_info()

# Create folder to hold output:
year = obs.data['time'][0].year
outdir = f"radar_data_{year:04d}/"
if not os.path.exists(outdir):
    os.mkdir(outdir)

# Create an hourly time array:
n_hour = 24 * (obs.data['time'][-1] - obs.data['time'][0]).days
time = np.array([obs.data['time'][0] + dt.timedelta(hours=i)
                 for i in range(n_hour)])

# Create container for interpolated data:
interpd, interpm = {}, {}
for r in radars:
    interpd[r] = np.zeros(n_hour)
    interpm[r] = np.zeros(n_hour)

# Loop over all times, interpolating data to each station and saving results:
for i,t in enumerate(time):
    for r in radars:
        interpd[r][i], interpm[r][i] = obs(t, radars[r][1], radars[r][0])

# Save results as a pickle and as a series of ASCII files:
with open(outdir+f"all_radars_{year}.pkl", 'wb') as out:
    pickle.dump((time, interpd, interpm), out)

for r in radars:
    with open(outdir+f"{r}_{year:04d}.txt", 'w') as out:
       out.write(f"Station {r} at geolat={radars[r][0]}, geolon={radars[r][1]}\n")
       out.write("Time\tInst. B\tHourly Max B\n")
       for i, t in enumerate(time):
           out.write(f"{t}\t{interpd[r][i]:012.7f}\t{interpm[r][i]:012.7f}\n")

# Create plots to examine dB distribution:
for r in radars:
    label = f"{r} (lat={radars[r][0]:4.1f}$^{{\\circ}}$)"
    plot = obs.plot_distrib(comp1=interpd[r], comp2=interpm[r], clab=label)
    plot[0].savefig(outdir+f"distribution_{r}.png")
    plt.close('all')