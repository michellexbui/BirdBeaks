#!/usr/bin/env python3

'''
This file creates analysis figures to understand how close/far magnetometer
sites are from radar sites. Because this changes as mag stations go on and
offline or report bad data, this needs to be performed as a function of time.
'''

import os
import pickle

import numpy as np
import matplotlib.pyplot as plt

import BirdBeaks

# Known bad mags (zero data):
# M02, M11, TUL


years = np.arange(1995, 2019)
datadir = BirdBeaks.install_dir + 'data/mag_data/'


def build_gooddata():
    '''
    For all years, create boolean arrays showing which mags have good data
    at any given time.

    Stash into a pickle.
    '''

    time = np.array([], dtype=object)
    mags = {}
    for m in BirdBeaks.std_mags:
        mags[m] = np.array([], dtype=bool)

    for i in years:
        # Open pickle:
        with open(datadir + f'magdata_{i:04d}.pkl', 'rb') as f:
            data = pickle.load(f)

        # Append time, data to total data dir.
        # Convert to bool first tho.
        time = np.append(time, data['time'])
        for m in BirdBeaks.std_mags:
            if m in data:
                mags[m] = np.append(mags[m], np.isfinite(data[m]['bmax']))
            else:
                mags[m] = np.append(mags[m],
                                    np.zeros(data['time'].size, dtype=bool))

    # Save resulting data product to file:
    with open(datadir+'mag_gooddata.pkl', 'wb') as f:
        pickle.dump((time, mags), f)


def load_gooddata():
    '''
    Quickly load the pickled data availability file.

    Usage:
    time, mags = load_gooddata()
    '''

    if not os.path.exists(datadir + 'mag_gooddata.pkl'):
        print('Mag availability file not found; building...')
        build_gooddata()

    with open(datadir+'mag_gooddata.pkl', 'rb') as f:
        time, mags = pickle.load(f)

    return time, mags


def report_good_mags(time=None, mags=None, percent=75.0, verbose=True):
    '''
    Create a list of magnetometers that has data for a fraction of the time
    greater than `percent` (defaults to 75% of total time span.)

    Returns "good mag" list to user. If `verbose` is true, summary is
    printed to screen.
    '''

    # Check for data, load if missing.
    if time is None or mags is None:
        time, mags = load_gooddata()

    nTime = time.size
    good_mags = []

    for m in BirdBeaks.std_mags:
        perc = time[mags[m]].size/nTime
        if verbose:
            print(f"{m} -> {perc:06.2%}")

        if perc*100 >= percent:
            good_mags.append(m)

    return good_mags


def summarize_mags(time=None, mags=None):
    '''
    Create a broken bar chart that summarizes the availability of mag data
    over the period of interest.

    Keywords are the time and magnetometer availability arrays as calculated
    and stored by the `load_gooddata` function. If they are not given,
    they will be read from file or, if the file is not found, recalculated.

    Returns a figure and axes object.
    '''

    # Gimmee dat good spacepy style.
    from spacepy.plot import style
    style()

    # Check for data, load if missing.
    if time is None or mags is None:
        time, mags = load_gooddata()

    # Create figure/axes.
    fig = plt.figure(figsize=(8.5, 11))
    ax = fig.add_subplot(111)

    # Loop through each magnetometer finding periods where data exists.
    # MPL's broken_barh function needs start times and width of bar,
    # so save start when we enter a period of good data and find width
    # when we leave a period of good data.
    for iMag, m in enumerate(BirdBeaks.std_mags):
        intervals = []
        isTrue = False
        for i, x in enumerate(mags[m]):
            if x and not isTrue:
                isTrue = True
                tstart = time[i]
            elif isTrue and not x:
                isTrue = False
                intervals.append((tstart, time[i]-tstart))
        # Close final interval if last data point is True:
        if x and isTrue:
            intervals.append((tstart, time[-1]-tstart))
        ax.broken_barh(intervals, (iMag-.3, .6))

    # Customize/polish axes.
    ax.set_yticks(np.arange(len(BirdBeaks.std_mags)),
                  labels=BirdBeaks.std_mags)

    ax.set_ylim([-1, len(BirdBeaks.std_mags)])

    ax.set_xlabel('Time')
    ax.set_ylabel('Station Data Availability')
    fig.tight_layout()

    return fig, ax
