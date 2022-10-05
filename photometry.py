"""
Script to extract photometry from reduced meade images

TODO: determine where to run this

Assumptions:
    - Data live in data_dir
    - One folder in data_dir per-filter
    - Data for each filter live in per-filter dir in data_dir

Prior to running this script:
    - Open a given image (e.g. test.fits)
    - Place circular regions at the location of stars of interest
    - Note the aperture radius which best covers the bright stars being analysed
    - Save a ds9 region file using "Image" coordinates format
    - Name the region file like the image, but with .reg extension (e.g. test.reg)
    - Repeat for all images from which to extract photometry

data_dir:
    - biases
    - darks
    - master_bias/dark
    - B:
       - B flats
       - B master_flat
       - B data
       - B reduced data
    - Repeat per filter
"""
import os
import argparse as ap
import numpy as np
import pyregion
from astropy import units as u
from astropy.wcs import WCS
from ccdproc import (
    ImageFileCollection,
    CCDData
    )
import sep

# pylint: disable = invalid-name
# pylint: disable = redefined-outer-name
# pylint: disable = no-member

def arg_parse():
    """
    Argument parser settings

    Parameters
    ----------
    None

    Returns
    -------
    args : array-like
        Array of command line arguments

    Raises
    ------
    None
    """
    p = ap.ArgumentParser()
    p.add_argument('data_dir',
                   help='location of data')
    p.add_argument('filters',
                   help='comma separated list of filters (e.g. B,V,R,I)')
    p.add_argument('apertures',
                   help='comma separated list of aperture radii (e.g. 5,4,3,3)')
    return p.parse_args()

def get_image_list(directory='.', glob_include='*_r.fts'):
    """
    Make a list of what images are present in a given
    directory

    Parameters
    ----------
    directory : str
        The path to the folder to analyse for images
        Default = '.' (the current directory)

    Returns
    -------
        The ccdproc ImageFileCollection of that directory

    Raises
    ------
    None
    """
    return ImageFileCollection(directory, glob_include=glob_include)

def phot(filename, coords):
    """
    Measure the photometry of the given image at the positions
    requested.

    Parameters
    ----------
    filename : str
        The name of the file we are extracting photometry from
    coords : array
        Array with x, y and r in the columns
        One row per aperture to extract

    Returns
    -------
    ids : array
        Array of star IDs
    flux : array
        Array of flux measurments
    err : array
        Array of flux error measurments
    flux_w_sky : array
        Array of flux measurments, without subtracting sky background
    err_w_sky : array
        Array of flux error measurments,
        without subtracting sky background

    Raises
    ------
    None
    """
    # load the reduced image as numpy array
    data = CCDData.read(filename, unit=u.adu).data
    # fix the byte order
    data = data.byteswap().newbyteorder()

    # extract fluxes while subtracting background
    flux, err, _ = sep.sum_circle(data,
                                  coords[:, 0],
                                  coords[:, 1],
                                  coords[:, 2],
                                  subpix=0,
                                  bkgann=(15, 20),
                                  gain=1.0)

    # extract fluxes without subtracting background
    flux_w_sky, err_w_sky, _ = sep.sum_circle(data,
                                              coords[:, 0],
                                              coords[:, 1],
                                              coords[:, 2],
                                              subpix=0,
                                              gain=1.0)

    # make a sequential sequence of star ids
    ids = np.arange(len(flux))

    return ids, flux, err, flux_w_sky, err_w_sky

def save_photometry(filename, coords, ra, dec, ids,
                    flux, err, flux_w_sky, err_w_sky):
    """
    """
    # set up output filename
    outfile = f"{filename.split('.fts')[0]}.csv"
    # set format out output
    fmt = "%d,%.2f,%.2f,%.8f,%.8f,%.4f,%.4f,%.4f,%.4f"
    # set the header row
    hdr = "ID,X,Y,RA,Dec,Flux,Flux_err,Flux_w_sky,Flux_err_w_sky"
    # save the output
    np.savetxt(outfile,
               np.c_[ids, coords[:, 0], coords[:, 1], ra, dec,
                     flux, err, flux_w_sky, err_w_sky],
               header=hdr,
               fmt=fmt,
               delimiter=",")


if __name__ == "__main__":
    # load command line arguments
    args = arg_parse()

    # go to the data dir
    os.chdir(args.data_dir)

    # get a list of filters
    filts = args.filters.split(',')

    # get a list of photometry apertures as integers
    apers = list(map(int, args.apertures.split(',')))

    # assert we have two list of the same length
    assert len(filts) == len(apers), "Uneven number of filters and apertures!"

    # then per-filter
    for filt, aper in zip(filts, apers):
        # change into the per-filter directory
        os.chdir(filt)

        # get a list of images
        images = get_image_list()

        # do photometry for all files where regions exist
        for filename in images.files_filtered(imagetyp='LIGHT', filter=filt):
            # load the region file
            root = filename.split('.fts')[0]
            region_filename = f"{root}.reg"
            reg = pyregion.open(region_filename)

            # repack the coords into a numpy array
            coords = []
            for r in reg:
                coords.append(r.coord_list)
            coords = np.array(coords)

            # cast the 3rd column as the requested aperture
            coords[:, 2] = aper

            # subtract 1 from x and y coords from ds9
            # this is required as FITS is 1 indexed and Numpy is 0 indexed
            coords[:, 0] -= 1
            coords[:, 1] -= 1

            # TODO: add recentering!

            # convert the coords into ra/dec using WCS from image header
            w = WCS(filename)
            ra, dec = w.all_pix2world(coords[:, 0], coords[:, 1], 0)

            # do photometry on this image
            ids, flux, err, flux_w_sky, err_w_sky = phot(filename, coords)

            # save output file
            save_photometry(filename, coords, ra, dec, ids, flux, err, flux_w_sky, err_w_sky)

        # go back to top level directory
        os.chdir('../')

