#!/bin/env python
"""
Authors: David Kent, Tim Erwin, Tim Bedin, Damien Irving

Copyright 2014 CSIRO

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Convert a CDAT xml catalogue to a single netCDF file and/or crop
temporal and spatial dimensions.

"""

import os
import sys
import argparse

import numpy as np
import cdms2
if hasattr(cdms2, 'setNetcdfDeflateFlag'):
    cdms2.setNetcdfDeflateFlag(0)
    cdms2.setNetcdfDeflateLevelFlag(0)
    cdms2.setNetcdfShuffleFlag(0)
import cdtime


def list_nobounds(cf, ids=False):
    """Get the names of all the variables in a netCDF file."""

    bnds = [v.bounds for v in cf.variables.values() if 'bounds' in v.attributes]
    bnds += [a.bounds for a in cf.axes.values() if 'bounds' in a.attributes]
    nodim = [vid for vid in cf.variables.keys() if cf[vid].getOrder() == '']
    nonvar = bnds + nodim
    if ids:
        return [v for v, k in cf.variables.iteritems() if v not in nonvar]
    else:
        return [k for v, k in cf.variables.iteritems() if v not in nonvar]


def check_time_axis(tvar):
    """Check that the time-axis is monotonically increasing.

    When cdo functions fail mid-process they often output a file
    that has a non-sensical, non-monotonic time axis.

    """

    assert type(tvar) == cdms2.tvariable.TransientVariable

    time_values = tvar.getTime()[:]
    dt = np.diff(time_values)
    check = np.all(dt > 0)

    if not check:
        print "Time axis not monotonically increasing, skipping %s" %(tvar.id)

    return check      


def check_valid_range(tvar):
    """Check if the variable data falls within its valid range."""

    assert type(tvar) == cdms2.tvariable.TransientVariable

    if 'valid_range' in tvar.attributes and isinstance(tvar.valid_range, basestring):
        try:
            tvar.valid_range = np.fromstring(tvar.valid_range.strip('[]'),
                                             dtype=vtar.dtype,
                                             sep=' ')
        except:
            pass

    
def convert_lon(lon):
    """Convert a single longitude value to a floating point number.

    Input longitude can be string or float and in 
      -135, 135W, 225 or 225E format. 

    Output longitude lies in the range 0 <= lon <= 360.

    """

    lon = str(lon)
    
    if 'W' in lon:
        deg_east = 360 - float(lon[:-1]) 
    elif 'E' in lon:
        deg_east = float(lon[:-1])
    elif float(lon) < 0.0:
        deg_east = 360 + float(lon)
    else: 
        deg_east = float(lon)
    
    assert 0 <= deg_east <= 360, "Longitude must lie between 0-360E"
    
    return deg_east
    

def convert_lat(lat):
    """Convert a single latitude value to a floating point number.

    Input latitude can be string or float and in -24 or 24S format. 

    """

    lat = str(lat)

    if 'N' in lat.upper():
        lat = float(lat[:-1])
    elif 'S' in lat.upper():
        lat = float('-'+lat[:-1])
    else:
        lat = float(lat)

    return lat     


def main(var, infile, outfile,
         time_bounds=':', lon_bounds=':',
         lat_bounds=':', level_bounds=':'):
    """Run the program."""

    cf = cdms2.open(infile)

    if var == 'None':
        vars = list_nobounds(cf, ids=True)
    else:
        vars = [var]

    cfout = cdms2.createDataset(outfile)
    nwritten = 0

    lat_bounds = map(convert_lat, lat_bounds) if lat_bounds != ':' else lat_bounds
    lon_bounds = map(convert_lon, lon_bounds) if lon_bounds != ':' else lon_bounds
    if lon_bounds != ':':
        assert lon_bounds[0] <= lon_bounds[1], \
        "WEST_LON is not west of EAST_LON on a 0E - 360E interval"

    for var in vars:
        v = cf(var, time=time_bounds, longitude=lon_bounds,
               latitude=lat_bounds, level=level_bounds)

        time_check = check_time_axis(v)
        check_valid_range(v)

        if time_check:
            vout = cfout.write(v, axes=v.getAxisList(), id=v.id)
            if hasattr(v, 'name') and 'variable' not in v.name:
                vout.name = v.name
            nwritten += 1
        
    if nwritten == 0:
        cfout.close()
        os.remove(outfile)
        sys.exit(1)
        
    for att in cf.listglobal():
        setattr(cfout, att, cf.attributes[att])

    cfout.close()


if __name__ == '__main__':

    extra_info = """  The edges of specified bounds are included.
  To select a single time, lon, lat or level, set both bounds to the same value.   
  """
    
    description = 'Convert a CDAT xml catalogue to a single netCDF file and/or crop temporal and spatial dimensions'
    parser = argparse.ArgumentParser(description=description,
                                     epilog=extra_info,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument("variable", type=str, help="""Variable to extract. If 'None', all variables will be extracted.""")
    parser.add_argument("infile", type=str, help="Name of input netCDF file or cdscan xml catalogue file")
    parser.add_argument("outfile", type=str, help="Name of output netCDF file")

    parser.add_argument("--time_bounds", type=str, nargs=2, metavar=('START_DATE', 'END_DATE'),
                        help="Bounds of the time period to extract from infile [default = all times]. Date format is YYYY-MM-DD.")
    parser.add_argument("--lon_bounds", type=str, nargs=2, metavar=('WEST_LON', 'EAST_LON'),
                        help="Longitude bounds of the region to extract from infile. Can be -135, 135W, 225 or 225E format. [default = all longitudes].")
    parser.add_argument("--lat_bounds", type=str, nargs=2, metavar=('SOUTH_LAT', 'NORTH_LAT'),
                        help="Latitude bounds of the region to extract from infile. Can be in -46 or 46S format. [default = all latitudes].")
    parser.add_argument("--level_bounds", type=float, nargs=2, metavar=('BOTTOM_LEVEL', 'TOP_LEVEL'),
                        help="Vertical level bounds of the region to extract from infile [default = all vetical levels].")

    args = parser.parse_args()

    args.time_bounds = ':' if not args.time_bounds else args.time_bounds
    args.lon_bounds = ':' if not args.lon_bounds else tuple(args.lon_bounds)
    args.lat_bounds = ':' if not args.lat_bounds else tuple(args.lat_bounds)
    args.level_bounds = ':' if not args.level_bounds else tuple(args.level_bounds)

    main(args.variable, args.infile, args.outfile,
         time_bounds=args.time_bounds,
         lon_bounds=args.lon_bounds,
         lat_bounds=args.lat_bounds,
         level_bounds=args.level_bounds)

