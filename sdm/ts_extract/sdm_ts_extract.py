#!/usr/bin/env python
""" This is a specialised script to extract a time series from SDM CoD files.

It dumps straight to JSON format, and doesn't write out a netCDF file.

"""

import argparse

import netCDF4 as nc4

from cod_file import CodFile



def main(args):

    # Extract the required values from the cod file.
    awap_pattern = "/local/ep1_1/rr_calib/rr_calib_daily_0.05*.nc"
    input_awap = nc4.MFDataset(awap_pattern, aggdim="time")
    in_var = input_awap.variables["rr"]

    print("Input shape is: {}"
          .format(in_var.shape))

    # TODO: Use lat/lon instead of index.
    some_ts = in_var[:, 312, 554]

    # Load in the CoD file.
    cod = CodFile(args.cod_file)

    # Do a num_to_index thing
    times = input_awap.variables["time"]
    
    nc4.date2num
    # Pull out the results.
    

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument("cod_file", help="The path to the change-of-date file")

    args = parser.parse_args()

    main(args)
