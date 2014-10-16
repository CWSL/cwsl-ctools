#!/usr/bin/env python
"""
Filename:    version_safe_cdscan.py   

Description: Create a xml catalogue of NetCDF files using cdscan
Input:       List on XML files
Output:      XML catalogue file suitable for use with CDAT/UV-CDAT (cdms python library)

Author:      David Kent David.Kent@csiro.au
Revisions:   Tim Bedin Tim.Bedin@csiro.au
             Tim Erwin Tim.Erwin@csiro.au
Copyright:   CSIRO, 2011

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

import sys, re, os
from optparse import OptionParser
import subprocess
import numpy as np

#CDAT
import cdms2

def cdscan(inputs, output):
    cmds = ['cdscan', '-x', output] + inputs
    subprocess.Popen(cmds).wait()

def change_permissions(ifile):
    cmds = ['chmod', '775', ifile]
    subprocess.Popen(cmds).wait()

def overlaps(m, ms):
    for testm in ms:
        if int(m.group(1)) < int(testm.group(2)) and \
           int(m.group(2)) > int(testm.group(1)):
            return True
    return False

def check_time_axis(ifile):
    # Check the output to ensure that the time-axis is complete.
    c = cdms2.open(ifile)
    if 'time' in c.axes:
       t = c.axes['time']
       if len(t) <= 1:
           c.close()
           return 0


       # Need to allow time-axis with units in "days since ..." to
       # vary a little. 
       dt = t[1] - t[0]
       if t.units.startswith("days"):
           mindt = dt - 3
           maxdt = dt + 3
       else:
           mindt = dt
           maxdt = dt
       diff_ts = [elem[1] - elem[0] for elem in \
                  zip(t[:-1], t[1:])]
       #check = np.logical_and(mindt <= diff_ts,
       #                       maxdt >= diff_ts)
       #print mindt <= diff_ts
       check = t[1:][np.logical_or(diff_ts < mindt,diff_ts > maxdt)]

       if len(check) > 0:
           # Not constantly increasing time-axis.
           print('\nERROR:\tTime axis not consistently monotonically increasing.')
           print('\tCheck that input files represent entire time period')
           #Print Problem Files
           import cdtime
           print("\tBoundaries of problem time points")
           for tp in check:
               print('\t\t'),
               tindex = np.where(t==tp)[0][0]
               for invalid_t in t[tindex-1:tindex+1]:
                   print('%s,' % cdtime.reltime(invalid_t,t.units).tocomp()),
               print('\n')
           c.close()
           return 1

    c.close()
    return 0
    

def main(inputs, output, ignore=False):
    """Run the program.
    """
    vpat = re.compile(r'(v\d+)/')
    inputs_with_version = filter(vpat.search, inputs)
    if inputs_with_version:
        inputs_version_stripped = map(lambda s: vpat.sub('', s), inputs)
        inputs_versions = map(vpat.search, inputs)
        latest_versions = []
        handled = []
        for i in range(len(inputs)):
            if i in handled:
                continue
            current = inputs_version_stripped[i]
            if inputs_version_stripped.count(current) > 1:
                idxs = [j for j, f in enumerate(inputs_version_stripped) \
                        if f == current]
                versions = [inputs_versions[j] for j in idxs]
                greatest = versions.index(max(versions))
                greatest_idxs = idxs[greatest]
                latest_versions.append(inputs[greatest_idxs])
                handled += idxs
            else:
                latest_versions.append(inputs[i])
                handled.append(i)
        inputs = latest_versions

    # Some CMIP3 datasets have two files representing that same variable/
    # time-period. We want to strip out duplicates....
    #date_pat = re.compile(r'(\d{4,6})[\d-]*.*(\d{4,6})[\d-]*')
    date_pat = re.compile(r'(\d{4,10})-(\d{4,10})')
    inputs_with_dates = map(date_pat.search, inputs)
    if any(inputs_with_dates) and not all(inputs_with_dates):
        # limit only to those with dates
        newinputs = []
        for i, has_date in enumerate(inputs_with_dates):
            if has_date:
                newinputs.append(inputs[i])
        inputs = newinputs
    elif all(inputs_with_dates):
        used_so_far = []
        for i, has_date in enumerate(inputs_with_dates):
            if not overlaps(has_date, [t[0] for t in used_so_far]):
                used_so_far.append((has_date, inputs[i]))
            else:
                print 'Warning: file overlaps. Skipping. ' + inputs[i]
        inputs = [t[1] for t in used_so_far]


    for infile in inputs:
        if check_time_axis(infile):
            print("Error in time axis of file %s" % infile)
            sys.exit(1)

    cdscan(inputs, output)

    if ignore:
        return

    # Check the output to ensure that the time-axis is complete.
    if check_time_axis(output):
       print("\tRemoving file %s" % output)
       os.remove(output)
       sys.exit(1)
    
    # Change permissions for the cdscan.    
    change_permissions(output)

if __name__ == '__main__':

    usage = "usage: %prog [options] input output \n" + \
            "  input:\tInput file name\n"+\
            "  output:\tOutput file name"

    parser = OptionParser(usage=usage, version=__version__)
    parser.add_option("-i", "--ignore-check", 
                      action="store_true", dest="ignore", default=False,
                      help="Print the names of the files.")
    #parser.add_option("-y", "--num-years",
    #                  dest="numyears", default=None, type="int",
    #                  help="Try and concatenate total number of years, YEARS, from the end of the catalogue. start_date and end_date ignored. ")

    (options, args) = parser.parse_args()

    if len(args) < 2:
        parser.print_usage()
        sys.exit(1)

    main(args[:-1], args[-1], options.ignore)
