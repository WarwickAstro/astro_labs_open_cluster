"""
Load the master catalog of clusters and find the best
ones for observing from Warwick
"""

import argparse as ap
import pandas as pd
import numpy as np

def arg_parse():
    """
    """
    p = ap.ArgumentParser()
    p.add_argument('catalog_path',
                   help='path to catalog file')
    p.add_argument('mag_limit',
                   help='faint mag limit',
                   type=float)
    p.add_argument('pmem_limit',
                   help='membership probability limit',
                   type=float)
    return p.parse_args()

if __name__ == "__main__":
    args = arg_parse()

    # read the catalog
    catalog = pd.read_csv(args.catalog_path)

    # find list of unique targets
    clusters = list(set(catalog['Cluster']))

    bright_members = {}
    high_pmem_members = {}
    dec_members = {}
    visible, suitable = [], []
    radius = {}

    # loop over each cluster
    for cluster in clusters:
        loc = np.where(catalog['Cluster'] == cluster)[0]
        # fetch useful columns
        mag = catalog['Vmag'][loc]
        pmem = catalog['Pmem'][loc]
        ra = catalog['ra'][loc]
        dec = catalog['dec'][loc]
        # get number of bright objects
        bright_members[cluster] = np.sum(mag <= args.mag_limit)
        # get number of high pmem objects
        high_pmem_members[cluster] = np.sum(pmem >= args.pmem_limit)
        # get avg dec
        dec_members[cluster] = np.nanmean(catalog['dec'][loc])
        # determine diameter
        ra_w = np.std(ra)
        dec_w = np.std(dec)
        radius[cluster] = round(np.sqrt(ra_w**2 + dec_w**2)*60, 2)

        # is it visible?
        if dec_members[cluster] >= 10:
            visible.append(cluster)

            if radius[cluster] <= 10:
                suitable.append(cluster)

    clus, mems, rads = [],  [], []
    for cluster in suitable:
        clus.append(cluster)
        mems.append(high_pmem_members[cluster])
        rads.append(radius[cluster])

    temp = zip(mems, rads, clus)
    temp = sorted(temp, reverse=True)
    mems, rads, clus = zip(*temp)

    for m, r, c in zip(mems, rads, clus):
        print(c, m, r)
