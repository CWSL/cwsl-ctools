#!/usr/bin/env python
""" This is a specialised script to extract a time series from SDM CoD files.

It dumps straight to JSON format, and doesn't write out a netCDF file.

"""

import netCDF4 as nc4

import .cod_file



def main():

    # Extract the required values from the cod file.
    awap_pattern = ""

    input_awap = nc4.MFDataset(awap_pattern, aggdim="time")

    in_var = input_awap.variables["rr"]

    print("Input shape is: {}"
          .format(in_var.shape))

    # TODO: Use lat/lon instead of index.
    some_ts = in_var[:, 312, 554]

    # TODO: Make the time series from the COD files.
    # Make a random timeseries from the extracted one.
    outthing = rnd.choice(some_ts, size=100000,
                          replace=True)

    print(outthing.shape)
    print(outthing)

if __name__ == "__main__":

    main()
