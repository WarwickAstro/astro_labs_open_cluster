"""
Example usage of the pipeline
"""
import os
from openclusters.reduce import reduce
from openclusters.mkregions import mkregions
from openclusters.photometry import photometry

# SET UP PIPELINE
# data directory
data_dir = ""
# reference image name, used for making regions
reference_image = ""
# reference filter name, used for making regions
reference_filter = "R"
# path to open cluster catalog file
catalog_path = ""
# name of cluster being analysed
cluster_name = ""
# colour of regions in ds9
region_colour = "green"
# list of filters to analyse
filters = ["B", "V", "R", "I"]
# list of photometry aperture radii, one per filter
apertures = [4, 4, 4, 4]
# cluster membership probability lower limit
pl = 0.5
# cluster membership probability upper limit
pu = 1.0
# cluster members faint magnitude limit
mf = 15.0
# cluster members bright magnitude limit
mb = 10.0

# ASSERT THE INPUTS ARE CORRECT
assert len(filters) == len(apertures), "Uneven number of filters and apertures!"
assert pl < pu, "cluster membership probability lower limit must be less than upper limit!"
assert mb < mf, "cluster magnitude bright limit must be less than the faint limit!"

# REDUCE THE DATA
reduce(data_dir, filters)

# MAKE THE REGION FILES
mkregions(data_dir, reference_image, reference_filter,
          catalog_path, cluster_name, pl, pu, mf, mb,
          region_colour)

# STOP HERE, MANUALLY MAKE OTHER FILTER REGION FILES

# DO PHOTOMETRY ON THE DATA
photometry(data_dir, filters, apertures)
