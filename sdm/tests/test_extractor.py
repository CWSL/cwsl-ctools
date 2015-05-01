import numpy as np

from sdm.cod import CoD
from sdm.extractor import GriddedExtractor

data_extractor = GriddedExtractor(cod_base_dir=r'C:\Users\ywang\tmp\CMIP5_v2',
                                  mask_base_dir=r'C:\Users\ywang\tmp\Masks',
                                  gridded_base_dir=r'C:\Users\ywang\tmp\AWAP',
                                  verbose=True)

data, dates, lat, lon = data_extractor.extract('ACCESS1.0', 'historical', 'tas', '2', 'tmin')

GriddedExtractor.save_netcdf('tmp.nc', data, dates, lat, lon,
                             'ACCESS1.0', 'historical', 'tas', '2', 'tmin')

data2, dates, lat, lon = data_extractor.extract(
    *CoD.get_components_from_path(
        r'C:\Users\ywang\tmp\CMIP5_v2\ACCESS1.0_historical\tas\tmin\season_2\rawfield_analog_2'))

np.testing.assert_equal(data, data2)