from sdm.cod import CoD
from sdm.mask import Mask
from sdm.gridded import AwapDailyData

import numpy as np

class GriddedExtractor(object):
    def __init__(self, cod_base_dir=None, mask_base_dir=None, gridded_base_dir=None):
        self.cod_manager = CoD(base_dir=cod_base_dir)
        self.mask_manager = Mask(base_dir=mask_base_dir)
        self.awap_manager = AwapDailyData(base_dir=gridded_base_dir)

    def extract(self, model, scenario, region, season, predictant, cube=True):
        cod_dates = self.cod_manager.read_cod(model, scenario, region, season, predictant)
        mask = self.mask_manager.read_mask(region)
        data = self.awap_manager.read_data(predictant, cod_dates['adates'], mask)

        if cube:
            data, lat, lon = self.cubify(data, mask)

        return data

    @staticmethod
    def cubify(data, mask):
        """ Reshape the given data of shape (ndays, npoints) to (ndays, nlat, nlon)
        """
        lat = np.arange(-4450, -995, 5) / 100.0
        lon = np.arange(11200, 15630, 5) / 100.0
        idx_mask = np.where(mask != 0)
        idx_lat_min = np.min(idx_mask[0])
        idx_lat_max = np.max(idx_mask[0])
        idx_lon_min = np.min(idx_mask[1])
        idx_lon_max = np.max(idx_mask[1])

        lat_subsetted = lat[idx_lat_min: idx_lat_max]
        lon_subsetted = lon[idx_lon_min: idx_lon_max]

        mask_subsetted = mask[idx_lat_min: idx_lat_max + 1, idx_lon_min: idx_lon_max + 1]
        idx_mask_subsetted = np.where(mask_subsetted.reshape(mask_subsetted.size) != 0)[0]

        ret = np.full((data.shape[0], mask_subsetted.size), np.NaN)
        ret[:, idx_mask_subsetted] = data
        ret = ret.reshape((data.shape[0], mask_subsetted.shape[0], mask_subsetted.shape[1]))

        return ret, lat_subsetted, lon_subsetted

    def save_netcdf(self, data, dates, lat, lon):
        min_day_components = CoD.calc_dates(np.min(dates))
        max_day_components = CoD.calc_dates(np.max(dates))
        dates = np.arange(
            np.datetime64('%s-%02d-%02d'
                          % (
                min_day_components['yyyy'], min_day_components['mm'], min_day_components['dd'])),
            np.datetime64('%s-%02d-%02d'
                          % (
                max_day_components['yyyy'], max_day_components['mm'], max_day_components['dd']))) \
                - np.datetime64('1899-12-31')

        if len(data.shape) == 3:  # cubic
            pass
        else:  # array of vectors
            pass

if __name__ == '__main__':
    data_extractor = GriddedExtractor(cod_base_dir=r'C:\Users\ywang\tmp\CMIP5_v2',
                                      mask_base_dir=r'C:\Users\ywang\tmp\Masks',
                                      gridded_base_dir=r'C:\Users\ywang\tmp\AWAP')

    data = data_extractor.extract('ACCESS1.0', 'historical', 'tas', '2', 'tmin')
