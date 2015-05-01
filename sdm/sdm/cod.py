"""
Helper program that manages CoD files

y.wang@bom.gov.au
"""
import os
from datetime import datetime

import numpy as np


class CoD(object):
    def __init__(self, base_dir=None, verbose=False):
        self.base_dir = base_dir or os.getcwd()
        self.verbose = verbose

    @staticmethod
    def calc_dates(cod_dates):
        """
        Calculate the yyyy, mm, dd for the given CoD Dates list
        """
        yyyymms = cod_dates / 100 + 190000
        yyyys = yyyymms / 100
        mmdds = cod_dates % 10000
        mms = mmdds / 100
        dds = mmdds % 100

        return {
            'yyyy': yyyys,
            'mm': mms,
            'dd': dds,
            'mmdd': mmdds,
            'yyyymm': yyyymms,
        }

    @staticmethod
    def format_dates(cod_dates, format_str='%Y-%m-%d'):
        dates = [datetime.strptime(str(d), '%Y%m%d').date().strftime(format_str)
                 for d in cod_dates + 19000000]
        return np.array(dates)

    @staticmethod
    def get_components_from_path(cod_file_path):
        _, _, season = os.path.basename(cod_file_path).split('_')
        p = os.path.dirname(os.path.dirname(cod_file_path))
        predictand = os.path.basename(p)
        p = os.path.dirname(p)
        region_type = os.path.basename(p)
        p = os.path.dirname(p)
        fields = os.path.basename(p).split('_')
        if len(fields) == 2:
            model, scenario = fields
        else:
            model, scenario = fields[0], ''

        return model, scenario, region_type, season, predictand

    @staticmethod
    def get_modsce(model, scenario):
        if model in ['NNR', 'AWAP'] or scenario in [None, '', 'VALID']:
            return model
        else:
            return model + '_' + scenario

    def get_dirout(self, model, scenario, region_type, season, predictand):
        return os.path.join(self.base_dir or os.getcwd(),
                            CoD.get_modsce(model, scenario),
                            region_type,
                            predictand,
                            'season_%s' % season)

    def get_cod_file_path(self, model, scenario, region_type, season, predictand):
        cod_file_path = os.path.join(self.get_dirout(model, scenario, region_type, season, predictand),
                                     'rawfield_analog_%s' % season)
        if self.verbose:
            print 'cod file path: %s' % cod_file_path
        return cod_file_path

    @staticmethod
    def read(cod_file_path):
        """ Read from the given CoD file path
        """
        with open(cod_file_path) as ins:
            _, _, season = ins.readline().split()
            rdates = []
            adates = []
            edists = []
            for line in ins.readlines():
                if line.strip() != '':
                    fields = line.split()
                    rdates.append(fields[0])
                    adates.append(fields[1])
                    edists.append(fields[2])

        return {
            'rdates': np.array(rdates, dtype=int),
            'adates': np.array(adates, dtype=int),
            'edists': np.array(edists, dtype=float),
        }

    def read_cod(self, model, scenario, region_type, season, predictand):
        """ Given the model, scenario, region_type, season, predictand, locate the CoD file path and read its content
        """
        return CoD.read(self.get_cod_file_path(model, scenario, region_type, season, predictand))
