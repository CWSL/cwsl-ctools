#!/bin/env python
"""
SVN INFO: $Id: xml_to_nc_mod.py 1532 2014-09-04 04:31:14Z tae599 $
Filename:    
Author:      David Kent, ken244, David.Kent@csiro.au
Description: 
Input:       
Output:      

Copyright CSIRO, 2010
"""

__version__ = '$Revision: 1532 $'

import sys
from optparse import OptionParser
import subprocess
import os

import numpy as np
import cdms2
if hasattr(cdms2, 'setNetcdfDeflateFlag'):
    cdms2.setNetcdfDeflateFlag(0)
    cdms2.setNetcdfDeflateLevelFlag(0)
    cdms2.setNetcdfShuffleFlag(0)
import cdtime

import pdb


############
# Main
############

def recall_files(cf, var):

    # Test to see if dmget exists..
    ret = subprocess.Popen(['which', 'dmget']).wait()
    if ret != 0:
        return

    # dmget exists so try and recall underlying files
    all = []
    v = cf[var]

    if not v:
        return

    all.append(os.path.join(cf.datapath, 
                            v.getPaths()[0][0]))

    # Retrieve from tape
    if all:
        print ' '.join(['dmget', '-a'] + all)
        ret = subprocess.Popen(['dmget', '-a'] + all).wait()
        if ret:
            sys.exit('Subprocess failed.')
    return

def split_date(sdate,start_of_year=True):

    month,day = (1,1)
    if not start_of_year:
        month,day = 12,31

    if len(sdate) == 4:
        year = int(sdate)  
    elif len(sdate) == 6:
        year = int(sdate[0:4])
        month = int(sdate[4:])
        if not start_of_year:
            day = days_in_month(year,month)
    elif len(sdate) == 8:
        year = int(sdate[0:4])
        month = int(sdate[4:6])
        day = int(sdate[6:])

    return year,month,day

def days_in_month(year,month,cal=False):

    import calendar
    weekday,num_days = calendar.monthrange(year,month)
    return num_days

def main(var, incat, output,
         force,start_year=None,end_year=None):
    """Run the program.
    
    @param var: The variable to extract from the catalouge.
    @type  var: string
    @param input: single or list of input files
    @type  input: list or string
    @param output: File to output list of actual netCDF files to
    @type  output: string
    @param force: If True then existing files will be overwritten. If false then
                  they will be skipped.
    @type  force: boolean
    """
    #
    # Get subset from catalogues
    #
    if not force and os.access(output, os.F_OK):
        return

    if start_year and end_year:
        syear,smonth,sday = split_date(start_year)
        eyear,emonth,eday = split_date(end_year,False)
        start_year = cdtime.comptime(syear,smonth,sday)
        end_year = cdtime.comptime(eyear,emonth,eday)

    cf = cdms2.open(incat)

    if var == 'None':
        from cct.cct import list_nobounds
        vars = list_nobounds(cf, ids=True)
    else:
        vars = [var]

    recall_files(cf, vars[0])

    cfout = cdms2.createDataset(output)
    nwritten = 0
    for var in vars:
        try:
            if start_year and end_year:
                #Check time axis
                v = cf(var,time=(start_year,end_year,'cc'))
                t = v.getTime()
                v_start_year = cdtime.reltime(t[0],t.units).tocomp(t.getCalendar())
                v_end_year = cdtime.reltime(t[-1],t.units).tocomp(t.getCalendar())

                if not (v_start_year.year == start_year.year and \
                        v_start_year.month == start_year.month and \
                        v_end_year.year == end_year.year and \
                        v_end_year.month == end_year.month):

                    raise Exception("Time axis does not contain requested period, Request (%s - %s), Actual (%s - %s)" %
                                    (start_year.year,end_year.year,v_start_year.year,v_end_year.year))
            else:
                v = cf(var)
            current_time = v.getTime()
            if current_time is None: raise Exception('Not time axis.')
        except Exception, e:
            # Probably no data in file...
            print 'WARNING: skipping variable, %s, in file ' % var, incat
            print str(e)
            continue
        
        # Check that the time-axis is monotonically increasing...
        # We need to discover the time gap between adjacent points
        # then test that it lies within the correct range.
        time_axis = v.getTime()

        # Make a test difference between two adjacent time steps.
        testdiff = time_axis[2] - time_axis[1]
        
        if testdiff == 1:
            # daily
            tol = (1, 1)
         
        elif 28 <= testdiff <= 31:
            # monthly
            tol = (28, 31)
         
        elif 360 <= testdiff <= 366:
            # yearly
            tol = (360, 366)
         
        diffs = time_axis[1:] - time_axis[:-1]

        # check if any differences are outside bounds
        if any(d < tol[0] or d > tol[1] for d in diffs):
            print 'WARNING: incomplete time axis. Skipping ', var
            cfout.close()
            os.remove(output)
            sys.exit(0)
            
        if 'valid_range' in v.attributes and isinstance(v.valid_range,
                                                        basestring):
            try:
                v.valid_range = np.fromstring(v.valid_range.strip('[]'),
                                              dtype=v.dtype,
                                              sep=' ')
            except:
                pass


        # Check if any axes are of type float32 instead of float64
        # This is due to a known bug in cdat < 6.0
        # TODO: Update to a newer version of cdat or learn how to construct
        # non-rectangular grids with cdms2.
        
        # Try to deal with situations were variables in the file do not have 
        # latitude or longitude axis.
        try:
            if v.getLatitude().dtype == 'float32' or v.getLongitude().dtype == 'float32':
                # This is a hack to get around the bug in cdat < 6.0 that stops netcdf
                # files being written out if their lat or lon are floats rather
                # than doubles.
                print("### WARNING - File has float coordinate variables instead of doubles ###")
                print("    Making multiple attempts to write out file")

                attempts = 0
                done = False
                while attempts < 4 and not done:
                    try:
                        vout = cfout.write(v, id = v.id, axes = v.getAxisList())
                        print("Written!")
                        done = True
                    except TypeError:
                        attempts += 1
                        print("Failed attempts = " + str(attempts))
                        continue
                    
            else:
                vout = cfout.write(v, axes = v.getAxisList(), id=v.id)
        # Catching non-lat/lon variables.
        except AttributeError:
            vout = cfout.write(v, axes = v.getAxisList(), id=v.id)
  
        if hasattr(v, 'name') and 'variable' not in v.name:
            vout.name = v.name
        nwritten += 1
        
    if nwritten == 0:
        cfout.close()
        os.remove(output)
        sys.exit(1)
        
    for att in cf.listglobal():
        setattr(cfout, att, cf.attributes[att])

    cf.close()
    cfout.close()


############
# Run control
############
if __name__ == '__main__':

    usage = "usage: %prog [options] variable incat outfile \n" + \
            "  variable:\tVariable to extract\n" + \
            "  incat:\tCatalogue file to operate on\n"+\
            "  outfile:\tNetCDF file to output to"

    parser = OptionParser(usage=usage, version=__version__)
    parser.add_option("-o", "--force", 
                      action="store_true", dest="force", default=False,
                      help="Force the overwrite of existing outputs")
    parser.add_option("-s", "--start_year", 
                      dest="start_year",default=None,
                      help="Start year to trim dataset")
    parser.add_option("-e", "--end_year",default=None,
                      dest="end_year",
                      help="End year to trim dataset")

    (options, args) = parser.parse_args()

    if len(args) != 3:
        parser.print_usage()
        sys.exit()

    var, incat, output = args
    main(var, incat, output, 
         options.force,options.start_year,options.end_year)
