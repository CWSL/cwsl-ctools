import os

from scipy.io import netcdf


class Mask(object):

    def __init__(self, base_dir=None):
        self.base_dir = base_dir or os.getcwd()

    def read_mask(self, region_name):
        file_path = os.path.join(self.base_dir, 'mask_%s.nc' % region_name)
        ncd_file = netcdf.netcdf_file(file_path)
        mask = ncd_file.variables['mask'].data.copy()

        return mask