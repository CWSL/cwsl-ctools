import os
from datetime import date, timedelta

import numpy as np
from scipy.io import netcdf

from sdm.cod import CoD
from sdm.mask import Mask
from sdm.gridded import AwapDailyData


class GriddedExtractor(object):
    def __init__(self, cod_base_dir=None, mask_base_dir=None, gridded_base_dir=None, verbose=False):
        self.cod_manager = CoD(base_dir=cod_base_dir, verbose=verbose)
        self.mask_manager = Mask(base_dir=mask_base_dir, verbose=verbose)
        self.awap_manager = AwapDailyData(base_dir=gridded_base_dir, verbose=verbose)

    def extract(self, model, scenario, region_type, season, predictant, region=None, cube=True):
        cod_dates = self.cod_manager.read_cod(model, scenario, region_type, season, predictant)
        mask = self.mask_manager.read_mask(region or region_type)
        data = self.awap_manager.read_data(predictant, cod_dates['adates'], mask)

        if cube:
            data, lat, lon = self.cubify(data, mask)
        else:
            lat, lon = self.awap_manager.lat, self.awap_manager.lon

        return data, cod_dates['rdates'], lat, lon

    def extract_with_cod_file(self, cod_file_path, region=None, cube=True):
        _, _, season = os.path.basename(cod_file_path).split('_')
        p = os.path.dirname(os.path.dirname(cod_file_path))
        predictant = os.path.basename(p)
        p = os.path.dirname(p)
        region_type = os.path.basename(p)
        p = os.path.dirname(p)
        model, scenario = os.path.basename(p).split('_')

        return self.extract(model, scenario, region_type, season, predictant, region, cube=cube)

    @staticmethod
    def cubify(data, mask):
        """ Reshape the given data of shape (ndays, npoints) to (ndays, nlat, nlon)
        """
        lat = np.arange(-4450, -995, 5) / 100.0
        lon = np.arange(11200, 15630, 5) / 100.0
        idx_mask = np.where(mask != 0)
        idx_lat_min = np.min(idx_mask[0])
        idx_lat_max = np.max(idx_mask[0]) + 1
        idx_lon_min = np.min(idx_mask[1])
        idx_lon_max = np.max(idx_mask[1]) + 1

        lat_subsetted = lat[idx_lat_min: idx_lat_max]
        lon_subsetted = lon[idx_lon_min: idx_lon_max]

        mask_subsetted = mask[idx_lat_min: idx_lat_max, idx_lon_min: idx_lon_max]
        idx_mask_subsetted = np.where(mask_subsetted.reshape(mask_subsetted.size) != 0)[0]

        ret = np.full((data.shape[0], mask_subsetted.size), np.NaN)
        ret[:, idx_mask_subsetted] = data
        ret = ret.reshape((data.shape[0], mask_subsetted.shape[0], mask_subsetted.shape[1]))

        return ret, lat_subsetted, lon_subsetted

    @staticmethod
    def save_netcdf(filename, data, dates, lat, lon,
                    model, scenario, region_type, season, predictant):

        min_day_components = CoD.calc_dates(np.min(dates))
        max_day_components = CoD.calc_dates(np.max(dates))

        sdate = date(min_day_components['yyyy'], min_day_components['mm'], min_day_components['dd'])
        edate = date(max_day_components['yyyy'], max_day_components['mm'], max_day_components['dd']) + timedelta(1)

        dates = (np.arange(np.datetime64(sdate), np.datetime64(edate)) - np.datetime64('1899-12-31')).astype('int')

        f = netcdf.netcdf_file(filename, 'w')
        f.title = 'Daily gridded climate series (%s, %s, %s, %s, %s)' % (
        model, scenario, region_type, season, predictant)
        f.institution = 'Bureau of Meteorology'
        f.source = 'Statistical Downscaling Model'
        f.history = 'Generated on %s' % date.today()

        f.createDimension('time', 0)
        var_time = f.createVariable('time', np.float32, ('time',))
        var_time[:] = dates
        var_time.units = 'days since 1899-12-31 00:00:00'
        var_time.calendar = 'standard'

        f.createDimension('lat', lat.size)
        var_lat = f.createVariable('lat', float, ('lat',))
        var_lat[:] = lat
        var_lat.units = 'degrees_north'
        var_lat.long_name = 'latitude'
        var_lat.standard_name = 'latitude'

        f.createDimension('lon', lon.size)
        var_lon = f.createVariable('lon', float, ('lon',))
        var_lon[:] = lon
        var_lon.units = 'degrees_east'
        var_lon.long_name = 'longitude'
        var_lon.standard_name = 'longitude'

        missing_value = 99999.9
        var_data = f.createVariable(predictant, np.float32, ('time', 'lat', 'lon'))
        data = data.copy()
        data[np.where(np.isnan(data))] = missing_value
        var_data[:, :, :] = data
        var_data.units = 'mm' if predictant == 'rain' else 'K'
        var_data.long_name = predictant
        var_data.missing_value = var_data._FillValue = missing_value

        f.close()


if __name__ == '__main__':
    data_extractor = GriddedExtractor(cod_base_dir=r'C:\Users\ywang\tmp\CMIP5_v2',
                                      mask_base_dir=r'C:\Users\ywang\tmp\Masks',
                                      gridded_base_dir=r'C:\Users\ywang\tmp\AWAP',
                                      verbose=True)

    data, dates, lat, lon = data_extractor.extract('ACCESS1.0', 'historical', 'tas', '2', 'tmin')

    GriddedExtractor.save_netcdf('tmp.nc', data, dates, lat, lon,
                                 'ACCESS1.0', 'historical', 'tas', '2', 'tmin')

    data2, dates, lat, lon = data_extractor.extract_with_cod_file(
        r'C:\Users\ywang\tmp\CMIP5_v2\ACCESS1.0_historical\tas\tmin\season_2\rawfield_analog_2')

    np.testing.assert_equal(data, data2)
