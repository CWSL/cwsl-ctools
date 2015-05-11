#!/usr/bin/env python
""" Extract a JSON time series from a netCDF file.

Returns a JSON object with an array of numerical
data and a corresponding array of ISO strings.

"""

import argparse
import json
import sys

import netCDF4 as nc4


def main(args):
    """ Extract a JSON timeseries from a netCDF file."""

    # Open the netCDF file
    input_file = nc4.Dataset(args.infile, 'r')

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
    output_times = nc4.num2date(time_var[:], time_var.units,
                                time_var.calendar)
    output_strings = [datething.isoformat()
                      for datething in output_times]

    # Close the netCDF file
    input_file.close()

    # Write it out using json.dumps
    output = {"times": output_strings,
              args.varname: output_data.tolist()}

    with open(args.outfile, 'w') as output_file:
        output_file.write(json.dumps(output))



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
