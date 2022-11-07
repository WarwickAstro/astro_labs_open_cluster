# Open Cluster Analysis Code

Scripts for 3rd year undergrad lab experiment

Data will be obtained using the campus observatory. Images will be solved
using astrometry.net at the observatory. The students will collect their
observations into the following directory structure:

```data_dir:
      - biases
      - darks
      - B:
         - B flats
         - B science data
      - V:
         - V flats
         - V science data
      - R:
         - R flats
         - R science data
      - I:
         - I flats
         - I science data
```

If a particular filter was not used, then obviously that directory is not
necessary. ```data_dir``` can be any folder on your storage area/laptop.
e.g. ```/Users/jmcc/data/20220909```.

All python scripts described below can be called with the ```-h``` option
to remind yourself of the required input parameters.

There are four steps to producing photometry:

   1. Collect the data into the structure described above
   1. Run the ```reduce.py``` script on this data directory.
   1. Run the ```mkregions.py``` script
   1. Run the ```photometry.py``` script

These scripts will calibrate the data, identify which stars to extract
photometry from and then perform the aperture photometry.

Finally the students must analyse the output photometry files to create
the HR diagrams and perform the analyse described in the experiment.

# Combined Analysis Notebook

The pipeline functions have been combined into one simple Jupyter notebook.
You must set up the pipeline by supplying the informatio in the setup cell.

Then you can run the reduction and make the region file for the reference filter.
This region file can then be copied and adjusted to line up the stars in the
other filters. Save a new aligned copy of the region file for each filter/image
to extract photometry from. Then continue to the photometry step.

# Individual Script Usage

### reduce.py

```
▶ python reduce.py -h
usage: reduce.py [-h] data_dir filters

positional arguments:
    data_dir    location of data
    filters     comma separated list of filters (e.g. B,V,R,I)

    optional arguments:
      -h, --help  show this help message and exit
```

### mkregions.py

```
▶ python mkregions.py -h
usage: mkregions.py [-h] [--region_colour {green,blue,red,yellow}]
                           data_dir reference_image {B,V,R,I} cluster_name
                           cmp_range mag_range catalog_path

positional arguments:
  data_dir              path to data on disc
  reference_image       name of reference image
  {B,V,R,I}             filter of reference image
  cluster_name          Name of cluster (e.g. NGC2099)
  cmp_range             cluster membership probability range, comma separated
                        - lower,upper (e.g. 0.5,1.0)
  mag_range             cluster magnitude range, comma separated -
                        faint,bright (e.g. 15.0,10.0)
  catalog_path          path to catalog file

optional arguments:
  -h, --help            show this help message and exit
  --region_colour {green,blue,red,yellow}
                        colour of regions
```

### photometry.py

```
▶ python photometry.py -h
usage: photometry.py [-h] data_dir filters apertures

positional arguments:
  data_dir    location of data
  filters     comma separated list of filters (e.g. B,V,R,I)
  apertures   comma separated list of aperture radii (e.g. 5,4,3,3)

optional arguments:
  -h, --help  show this help message and exit
```

# Experiment setup

I used the tic8 crossmatch script to get more magnitudes for the cluster memebers from the TIC8 catalog.

# Copntributors

James McCormac
