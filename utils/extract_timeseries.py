#!/usr/bin/env python
""" Extract a JSON time series from a netCDF file.

Returns a JSON object with an array of numerical
data and a corresponding array of ISO strings.

"""

import argparse
import re
import json
import sys
import datetime as dt

import scipy.io.netcdf as nc


def main(args):
    """ Extract a JSON timeseries from a netCDF file."""

    # Open the netCDF file
    input_file = nc.netcdf_file(args.infile, 'r',
                                mmap=False)

    # Grab the variable
    input_var = input_file.variables[args.varname]

    # Test that the required x and y fits.
    val_shape = input_var.shape
    if (args.x_val > input_var.shape[2] or
        args.y_val > input_var.shape[1]):
        input_file.close()
        print("ERROR: Given x or y vals are no good!")
        sys.exit(1)

    # Extract the data
    output_data = input_var[:, args.y_val, args.x_val]

    # Extract the associated times
    time_var = input_file.variables["time"]

    # This is a little brittle - this extraction makes an
    # assumption about the use of a standard calendar.
    units_re = r"^(?P<unit>\S+) since (?P<year>\d+)-(?P<month>\d+)-(?P<day>\d+).+$"

    match_dict = re.match(units_re, time_var.units).groupdict()
    start_date = dt.date(int(match_dict["year"]), int(match_dict["month"]),
                         int(match_dict["day"]))
    
    if match_dict["unit"] != "days":
        raise Exception("Time unit: {} not understood"
                        .format(match_dict["unit"]))
    if time_var.calendar != "standard":
        print("WARNING: calendar {} is not standard. JSON date output may be incorrect"
              .format(time_var.calendar))
    
    output_times = map(lambda date: start_date + dt.timedelta(days=int(date)),
                       time_var)

    output_strings = [datething.isoformat()
                      for datething in output_times]

    # Write it out using json.dumps
    output = {"times": output_strings,
              args.varname: output_data.tolist()}

    with open(args.outfile, 'w') as output_file:
        output_file.write(json.dumps(output))

    # Close the netCDF file
    input_file.close()


if __name__ == "__main__":

    parser = argparse.ArgumentParser("Extract a JSON timeseries from a netCDF")
    parser.add_argument("infile", help="The input netCDF")
    parser.add_argument("outfile", help="The output JSON")
    parser.add_argument("varname", help="The variable to extract")
    parser.add_argument("x_val", help="The x value to extract",
                        type=int)
    parser.add_argument("y_val", help="The y value to extract",
                        type=int)

    args = parser.parse_args()

    main(args)
