"""
Helper program that manages CoD files

y.wang@bom.gov.au
"""
import os
import argparse

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
    def get_modsce(model, scenario):
        if model in ['NNR', 'AWAP'] or scenario in [None, '', 'VALID']:
            return model
        else:
            return model + '_' + scenario

    def get_dirout(self, model, scenario, region_type, season, predictant):
        return os.path.join(self.base_dir or os.getcwd(),
                            CoD.get_modsce(model, scenario),
                            region_type,
                            predictant,
                            'season_%s' % season)

    def get_cod_file_path(self, model, scenario, region_type, season, predictant):
        cod_file_path = os.path.join(self.get_dirout(model, scenario, region_type, season, predictant),
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

    def read_cod(self, model, scenario, region_type, season, predictant):
        """ Given the model, scenario, region_type, season, predictant, locate the CoD file path and read its content
        """
        return CoD.read(self.get_cod_file_path(model, scenario, region_type, season, predictant))


if __name__ == '__main__':
    """ The main program is to print the full file path to a CoD file given the input parameters
    """
    ap = argparse.ArgumentParser(prog=os.path.basename(__file__))
    ap.add_argument('-m', '--model', required=True, help='model name')
    ap.add_argument('-c', '--scenario', required=False, help='scenario name, e.g. historical, rcp45, rcp85')
    ap.add_argument('-r', '--region-type', required=True, help='pre-defined region type name, e.g. sea, sec, tas ...')
    ap.add_argument('-s', '--season', required=True, help='season number, e.g. 1 (DJF), 2 (MAM), 3 (JJA), or 4 (SON)')
    ap.add_argument('-p', '--predictand', required=True, help='predictand name, e.g. rain, tmax, tmin')
    ap.add_argument('--base-dir', required=False,
                    help='Base directory where CoD files are stored, default to the current working directory')

    ns = ap.parse_args()

    print CoD(ns.base_dir).get_cod_file_path(ns.model, ns.scenario, ns.region_type, ns.season, ns.predictand)
