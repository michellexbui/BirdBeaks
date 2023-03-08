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

import supermag
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

    # Save mag info to a CSV file.
    mag_info = supermag.read_statinfo()
    with open(datadir + 'mag_station_info.csv', 'w') as f:
        f.write('Station Name, geo lon, geo lat, data coverage\n')
        for m in BirdBeaks.std_mags:
            perc = 100. * time[mags[m]].size/nTime
            f.write(f"{m}, {mag_info[m]['geolon']:06.2f}, ")
            f.write(f"{mag_info[m]['geolat']:06.2f}, {perc:06.2f}\n")

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


def calc_distance(time=None, mags=None, write_single=True):
    '''
    For each radar station, find the nearest magnetometer with good data
    and calculate the lat and lon distance to that station as a function of
    time.

    Results are returned to user and also saved as a python pickle.
    '''

    # Convenience variables:
    nMag = len(BirdBeaks.std_mags)

    # Check for data, load if missing.
    if time is None or mags is None:
        time, mags = load_gooddata()

    # Get radar lat/lons:
    radars = BirdBeaks.load_radar_info()

    # Get magnetometer locations:
    # Load magnetometer info:
    mag_info = supermag.read_statinfo()

    # Create dictionaries of angular distances in lat/lon.
    # Also create containers for final results:
    dist_lat, dist_lon = {}, {}
    dLat, dLon = {}, {}
    for s in radars:
        dLat[s], dLon[s] = np.zeros(time.size), np.zeros(time.size)
        dist_lat[s] = np.zeros(nMag)
        dist_lon[s] = np.zeros(nMag)
        for imag, m in enumerate(BirdBeaks.std_mags):
            dist_lat[s][imag] = np.abs(radars[s][0] - mag_info[m]['geolat'])
            dist_lon[s][imag] = np.abs(radars[s][1] - mag_info[m]['geolon'])

    # Create magnetometer filter for good data only:
    filter = np.zeros(nMag, dtype=bool)

    # Now, obtain distance as a function of time:
    for i in range(time.size):
        for imag, m in enumerate(BirdBeaks.std_mags):
            filter[imag] = mags[m][i]
        for s in radars:
            dLat[s][i] = dist_lat[s][filter].min()
            dLon[s][i] = dist_lon[s][filter].min()

    if write_single:
        with open(datadir+'radar_mag_distance.pkl', 'wb') as f:
            pickle.dump((time, dLat, dLon), f)
    else:
        for s in radars:
            with open(datadir + f'radar_{s}_mag_dist.pkl', 'wb') as f:
                pickle.dump((time, dLat[s], dLon[s]), f)

    return dLat, dLon


def viz_distances(time=None, dLat=None, dLon=None):
    '''
    Create plots that visualize the lat/lon differences between stations
    and ground magnetometer stations.

    First 3 kwargs should be the time, dLat, and dLon data as calculated
    from `calc_distance` function above. If not present, they will be read
    from a Python pickle.
    '''

    # Load data if it's not handed over:
    if time is None or dLat is None or dLon is None:
        with open(datadir+'radar_mag_distance.pkl', 'rb') as f:
            time, dLat, dLon = pickle.load(f)

    # Get radar lat/lons:
    radars = BirdBeaks.load_radar_info()

    # Start by creating a stand-alone figure demonstrating how things
    # typically vary for a sample station.
    station = 'KLCH'
    f1, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    ax1.plot(time, dLon[station])
    ax2.plot(time, dLat[station])
    ax2.set_xlabel('Time')
    ax1.set_ylabel('$\\Delta Lon$ ($^{\\circ}$)')
    ax2.set_ylabel('$\\Delta Lat$ ($^{\\circ}$)')
    ax1.set_title(f'Offset to Nearest Mag: {station}')
    f1.tight_layout()

    # Now, prepare to show distribution of angular distances by
    # ordering radar stations by median lon distance.
    med_lon, med_lat = [], []
    r_names = list(radars.keys())
    for r in r_names:
        med_lon.append(np.median(dLon[r]))
        med_lat.append(np.median(dLat[r]))
    r_sort_lon = [x for _, x in sorted(zip(med_lon, r_names))]
    r_sort_lat = [x for _, x in sorted(zip(med_lat, r_names))]

    # Now, re-order data following our station order:
    lon_sort, lat_sort = [], []
    for r in r_sort_lon:
        lon_sort.append(dLon[r])
    for r in r_sort_lat:
        lat_sort.append(dLat[r])

    # Plot sorted boxplot distributions:
    f2, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    ax1.set_title('Offset to Nearest Magnetometer')
    ax1.boxplot(lon_sort, whis=1000, showfliers=False, labels=r_sort_lon)
    ax2.boxplot(lat_sort, whis=1000, showfliers=False, labels=r_sort_lat)

    # Polish up/label axes:
    ax1.set_xticklabels(r_sort_lon, rotation=90)
    ax2.set_xticklabels(r_sort_lat, rotation=90)
    ax1.set_ylabel('$\\Delta Lon$ ($^{\\circ}$)')
    ax2.set_ylabel('$\\Delta Lat$ ($^{\\circ}$)')
    ax2.set_xlabel('Radar Station')
    f2.tight_layout()


def convert_distances_csv():
    '''
    Convert pickles to CSV files.
    '''

    with open(datadir+'radar_mag_distance.pkl', 'rb') as f:
        time, dLat, dLon = pickle.load(f)
    radars = BirdBeaks.load_radar_info()

    for r in radars:
        with open(f"{r}_distance.csv", 'w') as f:
            f.write(f'Angular distance between radar {r} and nearest ' +
                    'magneteometer station with good data.\n')
            f.write('Time,dLon,dLat\n')
            for t, dlon, dlat in zip(time, dLon[r], dLat[r]):
                f.write(f"{t.isoformat()}, {dlon:06.3f}, {dlat:06.3f}\n")
