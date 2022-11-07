"""
Script to reduce images from meade telescope

TODO: determine where to run this

Assumptions:
    - Data live in data_dir
    - Biases/darks live in data_dir
    - One folder in data_dir per-filter
    - Flats for each filter live in per-filter dir in data_dir
    - Data for each filter live in per-filter dir in data_dir

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
from collections import defaultdict
from ccdproc import (
    CCDData,
    ImageFileCollection,
    combine,
    subtract_bias,
    subtract_dark,
    flat_correct,
    )
from astropy.io import fits
from astropy import units as u
import numpy as np

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
    return p.parse_args()

def get_image_list(directory='.', glob_exclude='master*'):
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
    return ImageFileCollection(directory, glob_exclude=glob_exclude)

def make_master_bias(images, bias_keyword='BIAS'):
    """
    If no master bias image is found try making a
    master bias using all biases found in the
    ImageFileCollection object, if any.

    Parameters
    ----------
    images : object ccdproc.ImageFileCollection
        Object containing a list of images in the
        working directory
    bias_keyword : str
        Header keyword for bias images
        Default = 'BIAS'

    Returns
    -------
    master_bias : array-like | None
        A master bias image array, or
        None if no biases are found

    Raises
    ------
    None
    """
    bias_list = []
    try:
        master_bias = CCDData.read('master_bias.fits', unit=u.adu)
        return master_bias
    except FileNotFoundError:
        # check for no images
        if not images.files:
            return None
        for f in images.files_filtered(imagetyp=bias_keyword):
            print(f)
            ccd = CCDData.read(f, unit=u.adu)
            bias_list.append(ccd)
    try:
        master_bias = combine(bias_list, method='median')
        master_bias.write('master_bias.fits', overwrite=True)
        return master_bias
    except IndexError:
        return  None

def make_master_dark(images, master_bias=None, dark_keyword='DARK',
                     exptime_keyword='EXPTIME'):
    """
    If no master dark image is found try making a
    master dark from all darks found in the
    ImageFileCollection object.

    If a master bias image is provided the darks
    are first corrected for their bias level
    before combination

    Parameters
    ----------
    images : object ccdproc.ImageFileCollection
        Object containing a list of images in the
        working directory
    master_bias : array-like, optional
        Array containing the master bias image
        Default = None
    dark_keyword : str
        Header keyword for dark images
        Default = 'DARK'
    exptime_keyword : str
        Header keyword for exposure time
        Default = 'EXPTIME'

    Returns
    -------
    master_dark : array-like | None
        A master dark image array, or
        None if no darks are found
    dark_exp : int | None
        The exposure time of the dark frames, or
        None if no darks are found

    Raises
    ------
    None
    """
    dark_list = []
    dark_exp = None
    try:
        fitsfile = 'master_dark.fits'
        master_dark = CCDData.read(fitsfile, unit=u.adu)
        dark_exp = int(fits.open(fitsfile)[0].header[exptime_keyword])
        return master_dark, dark_exp
    except FileNotFoundError:
        # check for no images
        if not images.files:
            return None, None
        for f in images.files_filtered(imagetyp=dark_keyword):
            print(f)
            if not dark_exp:
                with fits.open(f) as fitsfile:
                    dark_exp = int(fitsfile[0].header[exptime_keyword])
            ccd = CCDData.read(f, unit=u.adu)
            if master_bias:
                ccd = subtract_bias(ccd, master_bias)
            else:
                print('No master bias, skipping correction...')
            dark_list.append(ccd)
    try:
        master_dark = combine(dark_list, method='median')
        master_dark.write('master_dark.fits', overwrite=True)
        return master_dark, dark_exp
    except IndexError:
        return None, None

def make_master_flat(images, filt, master_bias=None, master_dark=None,
                     dark_exp=30, exptime_keyword='EXPTIME'):
    """
    If no master flat is found try making a master flat
    from all the flats in the ImageFileCollection
    object.

    If a master bias is provided the flats are first
    corrected for their bias level.

    Similarly, if a master dark is provided the flats
    are corrected for their dark current.

    Parameters
    ----------
    images : object ccdproc.ImageFileCollection
        Object containing a list of images in the
        working directory
    filt : str
        The name of the filter used for this data
    master_bias : array-like, optional
        Array containing the master bias image
        Default = None
    master_dark : array-like, optional
        Array containing the master dark image
        Default = None
    dark_exp : int, optional
        Exposure time for master dark
        Default = 30
    exptime_keyword : str, optional
        Header keyword for exposure time
        Default = 'EXPTIME'

    Returns
    -------
    master_flat : array-like | None
        A master flat image array, or
        None if no flats are found

    Raises
    ------
    None
    """
    # empty dictionaries for the filtered data
    flat_list = defaultdict(list)

    # look for master flat
    try:
        fitsfile = 'master_flat_{0:s}.fits'.format(filt)
        master_flat = CCDData.read(fitsfile, unit=u.adu)
        return master_flat
    except FileNotFoundError:
        # check for no images
        if not images.files:
            return None
        # determine the flat keyword
        nf = len(images.files_filtered(imagetyp='FLAT'))
        nff = len(images.files_filtered(imagetyp='Flat Field'))
        if nf > nff:
            flat_keyword = "FLAT"
        else:
            flat_keyword = "Flat Field"
        # create the master flat field for each filter
        print('Reducing flats from filter {0:s}'.format(filt))
        for f in images.files_filtered(imagetyp=flat_keyword, filter=filt):
            print(f)
            with fits.open(f) as fitsfile:
                data_exp = int(fitsfile[0].header[exptime_keyword])
            ccd = CCDData.read(f, unit=u.adu)
            if master_bias:
                ccd = subtract_bias(ccd, master_bias)
            else:
                print('No master bias, skipping correction...')
            if master_dark:
                ccd = subtract_dark(ccd, master_dark,
                                    scale=True,
                                    dark_exposure=dark_exp*u.second,
                                    data_exposure=data_exp*u.second)
            else:
                print('No master dark, skipping correction...')
            sky_level, sky_rms = estimate_sky_level(ccd.data)
            ccd.data = ccd.data/sky_level
            flat_list[filt].append(ccd)
    try:
        master_flat = combine(flat_list[filt], method='median')
        master_flat.write('master_flat_{0:s}.fits'.format(filt), overwrite=True)
    except IndexError:
        print('There are no flats for {0:s}, skipping...'.format(filt))
        master_flat = None
    return master_flat

def estimate_sky_level(data):
    """
    Function to interatively sigma clip the sky background
    to estimate the sky level without the influence of stars
    """
    mean_diff = 1E6
    mean_diff_limit = 1E-6
    sigma = 3
    # create a masked array where nothing is masked
    data = np.ma.masked_where(data < -1E6, data)
    i = 0
    while mean_diff > mean_diff_limit:
        mean = np.ma.average(data)
        rms = np.ma.std(data)
        masked_data = np.ma.masked_where(((data > mean+sigma*rms) | (data < mean-sigma*rms)), data)
        new_mean = np.ma.average(masked_data)
        new_rms = np.ma.std(masked_data)
        print('Sky level: {}, RMS: {}'.format(new_mean, new_rms))
        data = masked_data
        mean_diff = abs(new_mean-mean)/new_mean
    return new_mean, new_rms

def correct_data(filename, filt, master_bias=None, master_dark=None,
                 master_flat=None, dark_exp=30, exptime_keyword='EXPTIME'):
    """
    Correct a science image using the available
    master calibrations. Skip a calibration step if the
    master frame does not exist.

    Parameters
    ----------
    filename : str
        Name of the image to process
    filt : str
        The name of the filter used for this data
    master_bias : array-like, optional
        Array containing the master bias image
        Default = None
    master_dark : array-like, optional
        Array containing the master dark image
        Default = None
    master_flat : array-like, optional
        Array containing the master flat image
        Default = None
    dark_exp : int, optional
        Exposure time for master dark
        Default = 30
    exptime_keyword : str, optional
        Header keyword for exposure time
        Default = 'EXPTIME'

    Returns
    -------
    ccd : ccdproc.CCDData array
        The corrected image

    Raises
    ------
    None
    """
    print('Reducing {0:s}...'.format(filename))
    with fits.open(filename) as fitsfile:
        # collect/correct some header values
        hdr = fitsfile[0].header
        data_exp = int(hdr[exptime_keyword])

    ccd = CCDData.read(filename, unit=u.adu)
    if master_bias:
        ccd = subtract_bias(ccd, master_bias)
    else:
        print('No master bias, skipping correction...')
    if master_dark:
        ccd = subtract_dark(ccd, master_dark,
                            scale=True,
                            dark_exposure=dark_exp*u.second,
                            data_exposure=data_exp*u.second)
    else:
        print('No master dark, skipping correction...')
    if master_flat:
        ccd = flat_correct(ccd, master_flat)
    else:
        print('No master flat for {0:s}, skipping correction...'.format(filt))

    # after calibrating we get np.float64 data
    # if there are no calibrations we maintain dtype = np.uint16
    # sep weeps
    # fix this by doing the following
    if isinstance(ccd.data[0][0], np.uint16):
        ccd.data = ccd.data.astype(np.float64)

    # output the files
    new_filename = '{}_r.fts'.format(filename.split('.fts')[0])
    fits.writeto(new_filename, ccd.data, header=hdr, overwrite=True)
    return ccd

def reduce(data_dir, filters):
    """
    Combine the above and do the reduction
    for all filters in a given data_dir
    """
    # go to the data dir
    os.chdir(data_dir)

    # get a list of images
    images = get_image_list()

    # make master bias
    master_bias = make_master_bias(images)
    # make master dark
    master_dark, dark_exp = make_master_dark(images, master_bias=master_bias)


    # then per-filter
    for filt in filters:
        # change into the per-filter directory
        os.chdir(filt)

        # get a list of images
        images = get_image_list()

        # make master flat
        master_flat = make_master_flat(images,
                                       filt,
                                       master_bias=master_bias,
                                       master_dark=master_dark,
                                       dark_exp=dark_exp)

        # reduce each image, save reduced file
        for filename in images.files_filtered(imagetyp='LIGHT', filter=filt):
            data = correct_data(filename, filt,
                                master_bias=master_bias,
                                master_dark=master_dark,
                                master_flat=master_flat,
                                dark_exp=dark_exp)

        # go back to top level directory
        os.chdir('../')

if __name__ == "__main__":
    # load command line arguments
    args = arg_parse()

    # get a list of filters
    filts = args.filters.split(',')

    # run the reduction
    reduce(args.data_dir, filts)
