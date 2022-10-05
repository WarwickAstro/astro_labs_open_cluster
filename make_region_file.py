"""
"""
import sys
import os
import argparse as ap
import pandas as pd
import numpy as np
from astropy.wcs import WCS
from astropy.io import fits

# pylint: disable=invalid-name
# pylint: disable=redefined-outer-name

def arg_parse():
    """
    """
    p = ap.ArgumentParser()
    p.add_argument('data_dir',
                   help='path to data on disc')
    p.add_argument('reference_image',
                   help='name of reference image')
    p.add_argument('filter',
                   help='filter of reference image',
                   choices=['B', 'V', 'R', 'I'])
    p.add_argument('cluster_name',
                   help='Name of cluster (e.g. NGC2099)')
    p.add_argument('cmp_range',
                   help='cluster membership probability range, comma separated - lower,upper (e.g. 0.5,1.0)')
    p.add_argument('mag_range',
                   help='cluster magnitude range, comma separated - faint,bright (e.g. 15.0,10.0)')
    p.add_argument('catalog_path',
                   help='path to catalog file')
    p.add_argument('--region_colour',
                   help='colour of regions',
                   choices=['green', 'blue', 'red', 'yellow'],
                   default='green')
    return p.parse_args()

class Imager():
    """
    Constants for our imager
    """
    # exclusion zone size around the image edges
    border = 50
    # python vs C indexing for pyds9
    index_offset = 1
    # list of NITES filters
    filters = ['U', 'B', 'V', 'R', 'I', 'Clear']
    ra_keyword = 'RA'
    dec_keyword = 'DEC'
    image_keyword = 'LIGHT'
    flat_keyword = 'Flat Field'
    bias_keyword = 'BIAS'
    dark_keyword = 'DARK'
    dateobs_start_keyword = 'DATE-OBS'
    exptime_keyword = 'EXPTIME'

def catalogue_to_pixels(astrometry_image, catalogue_coords, object_ids):
    """
    Convert a list of catalogue positions to X and Y image
    coordinates

    Parameters
    ----------
    astrometry_image : str
        Name of the FITS file with solved WCS solution
    catalogue_coords : array-like
        RA and Dec in degrees of the targets positions to
        convert to pixels
    object_ids : array-like
        List of target matching IDs

    Returns
    -------
    x_checked : array-like
        X positions of stars found in the astrometry_image
    y_checked : array-like
        Y positions of stars found in the astrometry_image
    object_ids_checked : array-like
        Object IDs for the images found in the astrometry_image

    Raises
    ------
    None
    """
    # fetch header info
    try:
        with fits.open(astrometry_image) as fitsfile:
            hdr = fitsfile[0].header
            width = hdr['NAXIS1']
            height = hdr['NAXIS2']
    except FileNotFoundError:
        print('CANNOT FIND {}, EXITING...'.format(astrometry_image))
        sys.exit(1)

    # load the WCS
    w = WCS(hdr)
    # 0 is C indexing
    # 1 is Fortran indexing
    pix = w.all_world2pix(catalogue_coords, 1)
    x, y = pix[:, 0], pix[:, 1]
    # check that the pixel values are within the
    # bound of the image, exclude object if not
    x, y, object_ids = check_image_boundaries(x, y, object_ids, width, height)
    return x, y, object_ids

def check_image_boundaries(x, y, object_ids, width, height):
    """
    Check if a star is too close to the edge of an image

    Parameters
    ----------
    x : array-like
        X positions of stars to check
    y : array-like
        Y positions of stars to check
    object_ids : array-like
        List of object names for objects to check
    width : int
        CCD width in pixels
    height : int
        CCD height in pixels

    Returns
    -------
    x_checked : array-like
        X positions of objects safely on the image
    y_checked : array-like
        Y positions of objects safely on the image
    object_ids_checked : array-like
        Object IDs for objects safely on the image

    Raises
    ------
    None
    """
    x_checked, y_checked, object_ids_checked = [], [], []
    for i, j, k in zip(x, y, object_ids):
        if Imager.border < i < width-Imager.border:
            if Imager.border < j < height-Imager.border:
                x_checked.append(i)
                y_checked.append(j)
                object_ids_checked.append(k)
    return x_checked, y_checked, object_ids_checked


if __name__ == "__main__":
    args = arg_parse()

    # parse the probability range
    try:
        pl, pu = map(float, args.cmp_range.split(','))
        assert pl < pu, "cluster membership probability lower limit must be less than upper limit!"
    except ValueError:
        print('Enter a valid cluster membership probabilty range - lower,upper (e.g. 0.5,1.0')
        sys.exit(1)

    # parse the magnitude range
    try:
        mf, mb = map(float, args.mag_range.split(','))
        assert mb < mf, "cluster magnitude bright limit must be less than the faint limit!"
    except ValueError:
        print('Enter a valid magnitude range - faint,bright (e.g. 15.0,10.0')
        sys.exit(1)

    # load the catalog
    catalog = pd.read_csv(args.catalog_path)

    # remove spaces from Cluster names
    catalog['Cluster_n'] = [c.replace(' ', '') for c in catalog['Cluster']]

    # isolate the stars for the given cluster in the big catalog
    loc = np.where(catalog['Cluster_n'] == args.cluster_name)[0]
    coords = np.array([catalog['ra'][loc], catalog['dec'][loc]]).T
    ids = catalog['source_ID'][loc]

    # move into the data_dir for the reference filter
    os.chdir(f"{args.data_dir}/{args.filter}")

    # convert the catalogue positions into CCD coords and keep those on chip only
    x, y, oids = catalogue_to_pixels(args.reference_image, coords, ids)

    # output a region file with assumed raidius of 5 pixels
    region_filename = f"{args.reference_image.split('.fts')[0]}_test.reg"
    hdr = "# Region file format: DS9 version 4.1\nglobal color=green dashlist=8 3 width=1 font=\"helvetica 10 normal roman\" select=1 highlite=1 dash=0 fixed=0 edit=1 move=1 delete=1 include=1 source=1\nimage\n"
    with open(region_filename, 'w') as of:
        of.write(hdr)
        for i, j in zip(x, y):
            line = f"circle({i:.3f},{j:.3f},5) # color={args.region_colour}\n"
            of.write(line)
