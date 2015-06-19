#!/usr/bin/env python
"""
Command line interface to the Statistical Downscaling Model (SDM) package.
"""
import os
import sys
from ConfigParser import ConfigParser
import argparse

from sdm import __version__
from sdm.cod import CoD
from sdm.extractor import GriddedExtractor


def read_config(config_file):
    if not config_file:
        if 'USERPROFILE' in os.environ:  # Windows
            config_file = os.path.join(os.environ['USERPROFILE'], '.sdm.cfg')
        else:
            config_file = os.path.join(os.environ['HOME'], '.sdm.cfg')

    config = ConfigParser()
    config.optionxform = str  # preserve case
    config.read(config_file)

    return config


def main(args):
    ap = argparse.ArgumentParser(prog=os.path.basename(__file__),
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 description='',
                                 epilog=__doc__)

    ap.add_argument('-c', '--config-file',
                    required=False,
                    help='the configuration file, default to "$HOME/.sdm.cfg"')
    ap.add_argument('-V', '--verbose',
                    action='store_true',
                    default=False,
                    help='be more chatty')
    ap.add_argument('-v', '--version',
                    action='version',
                    version='%s: v%s' % (ap.prog, __version__))

    subparsers = ap.add_subparsers(dest='sub_command',
                                   title='List of sub-commands',
                                   metavar='sub-command',
                                   help='"%s sub-command -h" for more help' % ap.prog)

    cod_getpath_parser = subparsers.add_parser('cod-getpath',
                                               help='get the full path to a CoD file')

    cod_getpath_parser.add_argument('-m', '--model',
                                    required=True,
                                    help='model name')
    cod_getpath_parser.add_argument('-c', '--scenario',
                                    required=False,
                                    help='scenario name, e.g. historical, rcp45, rcp85')
    cod_getpath_parser.add_argument('-r', '--region-type',
                                    required=True,
                                    help='pre-defined region type name, e.g. sea, sec, tas ...')
    cod_getpath_parser.add_argument('-s', '--season',
                                    required=True,
                                    help='season number, e.g. 1 (DJF), 2 (MAM), 3 (JJA), or 4 (SON)')
    cod_getpath_parser.add_argument('-p', '--predictand',
                                    required=True,
                                    help='predictand name, e.g. rain, tmax, tmin')

    dxt_gridded_parser = subparsers.add_parser('dxt-gridded',
                                               help='extract gridded data using the given cod file')
    dxt_gridded_parser.add_argument('cod_file_path',
                                    help='full path to the CoD file')
    dxt_gridded_parser.add_argument('output_file',
                                    help='output netCDF file name')
    dxt_gridded_parser.add_argument('-R', '--region',
                                    required=False,
                                    help='the region where the data are to be extracted')

    dxt_gridded2_parser = subparsers.add_parser('dxt-gridded2',
                                                help='extract gridded data with the given parameters')
    dxt_gridded2_parser.add_argument('output_file',
                                     help='output netCDF file name')
    dxt_gridded2_parser.add_argument('-m', '--model',
                                     required=True,
                                     help='model name')
    dxt_gridded2_parser.add_argument('-c', '--scenario',
                                     required=False,
                                     help='scenario name, e.g. historical, rcp45, rcp85')
    dxt_gridded2_parser.add_argument('-r', '--region-type',
                                     required=True,
                                     help='pre-defined region type name, e.g. sea, sec, tas ...')
    dxt_gridded2_parser.add_argument('-s', '--season',
                                     required=True,
                                     help='season number, e.g. 1 (DJF), 2 (MAM), 3 (JJA), or 4 (SON)')
    dxt_gridded2_parser.add_argument('-p', '--predictand',
                                     required=True,
                                     help='predictand name, e.g. rain, tmax, tmin')
    dxt_gridded2_parser.add_argument('-R', '--region',
                                     required=False,
                                     help='the region where the data are to be extracted (default to region-type)')

    ns = ap.parse_args(args)

    config = read_config(ns.config_file)

    if ns.sub_command == 'cod-getpath':
        print CoD(config.get('dxt', 'cod_base_dir'), verbose=ns.verbose).get_cod_file_path(
            ns.model, ns.scenario, ns.region_type, ns.season, ns.predictand)

    elif ns.sub_command in ('dxt-gridded', 'dxt-gridded2'):
        gridded_extractor = GriddedExtractor(cod_base_dir=config.get('dxt', 'cod_base_dir'),
                                             mask_base_dir=config.get('dxt', 'mask_base_dir'),
                                             gridded_base_dir=config.get('dxt', 'gridded_base_dir'),
                                             verbose=ns.verbose)

        if ns.sub_command == 'dxt-gridded':
            model, scenario, region_type, season, predictand = CoD.get_components_from_path(ns.cod_file_path)
        else:
            model, scenario, region_type, season, predictand = \
                ns.model, ns.scenario, ns.region_type, ns.season, ns.predictand

        data, dates, lat, lon = gridded_extractor.extract(model, scenario, region_type, season, predictand,
                                                          ns.region)
        GriddedExtractor.save_netcdf(ns.output_file, data, dates, lat, lon,
                                     model, scenario, region_type, season, predictand)


if __name__ == '__main__':
    main(sys.argv[1:])

