import os

from scipy.io import netcdf


class Mask(object):

    def __init__(self, base_dir=None, verbose=False):
        self.base_dir = base_dir or os.getcwd()
        self.verbose = verbose

    def read_mask(self, region_name):
        file_path = os.path.join(self.base_dir, 'mask_%s.nc' % region_name)
        if self.verbose:
            print 'reading mask file: %s' % file_path
        ncd_file = netcdf.netcdf_file(file_path)
        mask = ncd_file.variables['mask'].data.copy()

        return mask