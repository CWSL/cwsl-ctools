#!/usr/bin/env python
""" This is a specialised script to extract a time series from SDM CoD files.

It dumps straight to JSON format, and doesn't write out a netCDF file.

"""

import json
import argparse

import netCDF4 as nc4

from cod_file import CodFile



def main(args):

    # Extract the required values from the cod file.
    awap_pattern = "/local/ep1_1/data/staging_data/AWAP/daily_0.05/rr_calib/rr_calib_daily_0.05*.nc"
    input_awap = nc4.MFDataset(awap_pattern, aggdim="time")
    in_var = input_awap.variables["rr"]

    #print("Input shape is: {}"
    #      .format(in_var.shape))

    lat_var = input_awap.variables["lat"]
    lon_var = input_awap.variables["lon"]

    # Grab the time series of interest.
    y_val = get_index(args.latitude, lat_var)
    x_val = get_index(args.longitude, lon_var)
    base_ts = in_var[:, y_val, x_val]

    # Load in the CoD file.
    cod = CodFile(args.cod_file)

    times = input_awap.variables["time"]
    indices = calculate_time_index(cod.projected_dates, times)

    input_awap.close()

    # Now pull out the required values.
    outts = base_ts[indices]

    # Write it out using json.dumps
    output_strings = [datething.isoformat()
                      for datething in cod.base_dates]

    output = {"times": output_strings,
              "rainfall": outts.tolist()}

    with open(args.outfile, 'w') as output_file:
        output_file.write(json.dumps(output))


def get_index(value, nc_var):
    """ Given a netCDF variable, get the index of a particular lat/lon point.

    Rounds to the nearest value.

    """

    n_steps = nc_var.shape[0] - 1
    var_range = nc_var[-1] - nc_var[0]
    step_size = var_range / n_steps

    #print("step_size is {}".format(step_size))

    change = float(value) - nc_var[0]
    index = int(round(change / step_size))

    return index


def calculate_time_index(datething, nc_time):
    """ Given a python datetime object, return the index of the matching time variable."""
    
    num_steps = nc_time.shape[0] - 1
    time_range = nc_time[-1] - nc_time[0]
    each_step = time_range / num_steps
    step = int(round(each_step))
    #print(each_step)
    #print(step)

    axis_numbers = nc4.date2num(datething, nc_time.units, nc_time.calendar)

    return_vals = (axis_numbers - nc_time[0]) / step

    return(return_vals.astype(int))


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument("latitude", help="The latitude of the the time-series to extract")
    parser.add_argument("longitude", help="The longitude of the time-series to extract")
    parser.add_argument("cod_file", help="The path to the change-of-date file")
    parser.add_argument("outfile", help="The path to write the output to")

    args = parser.parse_args()

    main(args)
