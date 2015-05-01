"""
Command line interface to the Statistical Downscaling Model (SDM) package.
"""
import os
import sys
import argparse


def main(args):
    ap = argparse.ArgumentParser(prog=os.path.basename(__file__),
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 description='',
                                 epilog=__doc__)

    ap.add_argument('-c', '--config-file',
                    required=False,
                    help='The configuration file, default to "$HOME/.sdm.cfg"')

    subparsers = ap.add_subparsers(dest='sub_command',
                                   title='List of sub-commands',
                                   metavar='sub-command',
                                   help='"%s sub-command -h" for more help' % ap.prog)

    cod_getpath_parser = subparsers.add_parser('cod-getpath',
                                               help='get the full path to a CoD file')

    cod_getpath_parser.add_argument('-m', '--model', required=True,
                                    help='model name')
    cod_getpath_parser.add_argument('-c', '--scenario', required=False,
                                    help='scenario name, e.g. historical, rcp45, rcp85')
    cod_getpath_parser.add_argument('-r', '--region-type', required=True,
                                    help='pre-defined region type name, e.g. sea, sec, tas ...')
    cod_getpath_parser.add_argument('-s', '--season', required=True,
                                    help='season number, e.g. 1 (DJF), 2 (MAM), 3 (JJA), or 4 (SON)')
    cod_getpath_parser.add_argument('-p', '--predictand', required=True,
                                    help='predictand name, e.g. rain, tmax, tmin')
    cod_getpath_parser.add_argument('--base-dir', required=False,
                                    help='Base directory where CoD files are stored, default to CWD')

    dxt_gridded_parser = subparsers.add_parser('dxt-gridded',
                                               help='extract gridded data')
    dxt_gridded_parser.add_argument('cod-file-path', help='full path to the CoD file')
    dxt_gridded_parser.add_argument('-r', '--region', required=False,
                                    help='The region where the data are to be extracted')

    ns = ap.parse_args(args)

    if ns.sub_command == 'cod-getpath':
        from sdm.cod import CoD

        print CoD(ns.base_dir).get_cod_file_path(
            ns.model, ns.scenario, ns.region_type, ns.season, ns.predictand)

    elif ns.sub_command == 'dxt-gridded':
        pass


if __name__ == '__main__':
    main(sys.argv[1:])

