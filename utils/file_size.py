#!/usr/bin/env python

import cdms2
import os, sys
from optparse import OptionParser

__version__ = "$rev$"

def get_filesize(ifile):

    try:
        fh = cdms2.open(ifile)
    except Exception, e:
        print("Cannot determine filesize: %s" % e)
        sys.exit(1)

    total = 0
    #
    try:
        for data_file in fh.getPaths():
            total += os.stat(os.path.join(fh.datapath,data_file)).st_size
    except:
        #Not a xml catalog?
        total += os.stat(ifile).st_size

    return total


if __name__ == "__main__":
    usage = "usage: %prog [options] ifile\n" + \
            "  ifile:\t\twill check size of ifile\n"
    parser = OptionParser(usage=usage, version=__version__)
    parser.add_option('-m', '--mbytes', dest='mbytes',
                      action="store_true",default=False, help='Return output in MB')

    (options, args) = parser.parse_args()
    if len(args) > 1:
        print("ERROR: incorrect number of arguments")
        print(usage)
        sys.exit(1)

    filesize = get_filesize(args[0])
    if options.mbytes:
        print(filesize/(1024*1024))
    else:
        print(filesize)
