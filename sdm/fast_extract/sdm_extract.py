#!/usr/bin/env python
""" This is a specialised script to extract a time series or histogram from SDM CoD files.

It dumps straight to JSON format, and doesn't write out a netCDF file.

"""

import json
import argparse
import string

import numpy as np
import netCDF4 as nc4

from cod_file import CodFile



def main(args):
    """ This script has not gone through a Code review

    - it should be checked before becoming a production service. This is
    because the exact date relationship between the reanalysis data
    and the AWAP data should be confirmed. AWAP data for rainfall is based
    on rain gauges, so the rainfall is recorded against the previous day.
    Is this the same for ERA-INT?

    """

    var_dict = {"rain": ("rr_calib", "rr", "rain"),
                "tmin": ("tmin", "tmin", "tmin"),
                "tmax": ("tmax", "tmax", "tmax")}

    this_var = var_dict[args.variable]

    # Extract the required values from the cod file.
    var_dict = dict(var_name=this_var[0])
    awap_pattern = string.Template("/local/ep1_1/data/staging_data/AWAP/daily_0.05/${var_name}/${var_name}_daily_0.05*.nc").substitute(var_dict)
    input_awap = nc4.MFDataset(awap_pattern, aggdim="time")
    in_var = input_awap.variables[this_var[1]]

    lat_var = input_awap.variables["lat"]
    lon_var = input_awap.variables["lon"]

    # Grab the time series of interest.
    y_val = get_index(args.latitude, lat_var)
    x_val = get_index(args.longitude, lon_var)
    base_ts = in_var[:, y_val, x_val]

    # Ensure the base timeseries is a masked array.
    base_ts = np.ma.masked_array(base_ts)

    # Load in the CoD file.
    cod = CodFile(args.cod_file)

    times = input_awap.variables["time"]
    indices = calculate_time_index(cod.projected_dates, times)

    input_awap.close()

    # Now pull out the required values.
    outts = base_ts[indices]

    # Filter bad values from the time series.
    out_dates, out_values, num_missing = filter_timeseries(cod.base_dates, outts, this_var[1])

    if args.output_type == "timeseries":
        output = write_timeseries(out_dates, this_var[2], out_values, num_missing)
    elif args.output_type == "histogram":
        output = write_histogram(out_dates, this_var[2], out_values, int(args.bins), num_missing)
    else:
        raise Exception("output_type: {} not understood"
                        .format(args.output_type))

    with open(args.outfile, 'w') as output_file:
        output_file.write(json.dumps(output))

def filter_timeseries(date_list, timeseries, var_name):
    """ Filter out invalid values in the timeseries."""

    num_bad = len(timeseries) - timeseries.count()

    # Filter out any masked (missing) values.
    to_keep = np.ma.getmaskarray(timeseries) == False

    output_ts = timeseries[to_keep]
    output_dates = np.array(date_list)[to_keep]

    # Remove anomalously low values from temperature fields.
    # (temps are in Kelvin)
    if var_name in ["tmax", "tmin"]:
        num_bad += sum(output_ts < 100.0)

        to_keep = output_ts >= 100.0
        output_ts = output_ts[to_keep]
        output_dates = output_dates[to_keep]

    return output_dates, output_ts, num_bad


def write_timeseries(date_list, variable_name,
                     timeseries, missing_vals):
    """ Create an output dictionary in timeseries form. """

    output_strings = [datething.isoformat()
                      for datething in date_list]

    output = {"times": output_strings,
              variable_name: timeseries.tolist(),
              "filtered_values": int(missing_vals)}

    return output

def write_histogram(date_list, variable_name,
                    timeseries, bins, missing_vals):
    """ Create an output dictionary in timeseries form. """

    # Use the numpy histogram calculator.
    counts, bins = np.histogram(timeseries, bins=bins)

    # Write it out using json.dumps
    # we write out the count in each bin, the
    # bins and the total number of entries.
    outbins = []
    for i in xrange(len(bins)-1):
        outbins.append("(" + str(bins[i]) + "," + str(bins[i+1]) + ")")

    output = {"bins": outbins,
              "counts": counts.tolist(),
              "num_entries": len(timeseries),
              "time_bounds": [date_list[0].isoformat(),
                              date_list[-1].isoformat()],
              "filtered_values": int(missing_vals)}

    return output


def get_index(value, nc_var):
    """ Given a netCDF variable, get the index of a particular lat/lon point.

    Rounds to the nearest value.

    """

    n_steps = nc_var.shape[0] - 1
    var_range = nc_var[-1] - nc_var[0]
    step_size = var_range / n_steps

    change = float(value) - nc_var[0]
    index = int(round(change / step_size))

    return index


def calculate_time_index(datething, nc_time):
    """ Given a python datetime object, return the index of the matching time variable."""

    num_steps = nc_time.shape[0] - 1
    time_range = nc_time[-1] - nc_time[0]
    each_step = time_range / num_steps
    step = int(round(each_step))

    axis_numbers = nc4.date2num(datething, nc_time.units, nc_time.calendar)

    return_vals = (axis_numbers - nc_time[0]) / step

    return(return_vals.astype(int))


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument("latitude", help="The latitude of the the time-series to extract")
    parser.add_argument("longitude", help="The longitude of the time-series to extract")
    parser.add_argument("variable", help="The variable name to extract")
    parser.add_argument("output_type", help="The type of output (histogram or timeseries)")
    parser.add_argument("bins", help="The number of bins for the output histogram")
    parser.add_argument("cod_file", help="The path to the change-of-date file")
    parser.add_argument("outfile", help="The path to write the output to")

    args = parser.parse_args()

    main(args)
