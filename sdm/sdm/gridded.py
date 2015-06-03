"""
Extract data from gridded dataset, i.e. AWAP daily dataset

y.wang@bom.gov.au
"""
import os

import numpy as np
from scipy.io import netcdf

from .cod import CoD


class AwapDailyData(object):

    def __init__(self, base_dir=None, verbose=False):
        self.resolution = '0.05'
        self.lat = np.arange(-4450, -995, 5) / 100.0
        self.lon = np.arange(11200, 15630, 5) / 100.0
        self.base_dir = base_dir or os.getcwd()
        self.verbose = verbose

    def read_one_file(self, var_name, year, month):
        if var_name in ['rr', 'rain']:
            var_code = 'rr'
            file_code = var_code + '_calib'
        else:
            var_code = var_name
            file_code = var_code

        file_path = os.path.join(self.base_dir,
                                 'daily_%s' % self.resolution,
                                 file_code,
                                 '%s_daily_%s.%04d%02d.nc' % (file_code, self.resolution, year, month))

        if self.verbose:
            print 'reading netcdf file: %s' % file_path
        ncd_file = netcdf.netcdf_file(file_path)
        var = ncd_file.variables[var_code]
        data = var.data.copy()
        data[np.where(var.data == var.missing_value)] = np.NaN
        ncd_file.close()

        return data

    def read_data(self, var_name, adates, mask):

        date_components = CoD.calc_dates(adates)

        idx_mask = np.where(mask.reshape(mask.size) != 0)[0]
        ret = np.empty((adates.size, idx_mask.size))
        ret[:] = np.NaN

        for yyyymm in sorted(set(date_components['yyyymm'])):
            data = self.read_one_file(var_name, yyyymm / 100, yyyymm % 100)
            data = data.reshape(data.shape[0], data.shape[1] * data.shape[2])

            idx_yyyymms = np.where(date_components['yyyymm'] == yyyymm)[0]
            idx_days = date_components['dd'][idx_yyyymms] - 1

            ret[idx_yyyymms, :] = data[idx_days, :][:, idx_mask]

        return ret




