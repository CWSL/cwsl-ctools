#!/usr/bin/env python
""" This script extracts the nino index time series

It takes in nino time series netCDF files, extracts the
data and then writes it out to a single JSON file.

It is quite specialised for use with the Nino34 web
interface.

"""

import argparse
import json

import netCDF4 as nc4


def main(input_list, outfile_name):
    """ Extract the nino/tos data from the files in the inputlist

    Save the results in JSON file 'outfile_name'.

    """

    # Extract the data into a dictionary.
    output_dict = {}
    for infile in input_list:

        this_dict = {}

        inds = nc4.Dataset(infile)
        model_name = inds.model_id

        in_var = inds.variables["tos"]
        time_var = inds.variables["time"]

        dates = nc4.num2date(time_var[:], time_var.units, time_var.calendar)
        data_series = in_var[:,0,0]

        this_dict["times"] = [str(timestep) for timestep in dates]
        this_dict["nino34"] = data_series.tolist()

        output_dict[model_name] = this_dict

    # Dump the dictionary to a JSON file.
    with open(outfile_name, 'w') as outfile:
        outfile.write(json.dumps(output_dict))


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument("inputfiles", help="The netCDF nino index timeseries",
                        nargs="+")
    parser.add_argument("outfile", help="The JSON file to write the results to")

    args = parser.parse_args()

    main(args.inputfiles, args.outfile)
