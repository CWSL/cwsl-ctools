#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" 

Description: Calculate the Niño 3.4 index from an input netCDF. 
             Requires program CDO (Climate Data Operators)

Authors:     Tim Bedin Tim.Bedin@csiro.au
Copyright:   2014 CSIRO

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

"""

import tempfile
import subprocess
import argparse

def main(infile, outfile):

    timeseries_tempfile = tempfile.NamedTemporaryFile()

    # Select the lon/lat box required
    # 170W to 120W, 5N to 5S.
    ts_call = ['cdo', '-s', '-fldmean',
               '-sellonlatbox,-170,-120,5,-5',
               infile,
               timeseries_tempfile.name]
    subprocess.call(ts_call)

    # Subtract the mean of the timeseries from the
    # timeseries to calculate the index.
    final_call = ['cdo', '-s', '-sub',
                  timeseries_tempfile.name,
                  '-timmean', timeseries_tempfile.name,
                  outfile]
    subprocess.call(final_call)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Calculate the Niño 3.4 index from an input sea surface temperature file.')
    parser.add_argument('input', help='input sea surface temperature netCDF')
    parser.add_argument('output', help='output netCDF Niño 3.4 timeseries ')
    args = parser.parse_args()

    main(args.input, args.output)
