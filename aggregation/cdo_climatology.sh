#!/bin/bash

#################################################################################################
# Authors:  Tim Bedin (Tim.Bedin@csiro.au)
#           Tim Erwin (Tim.Erwin@csiro.au)
#
# Copyright 2014 CSIRO
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Calculate a climatology given a timespan. Sets the timeaxis to the mid point of the timespan. 
# Requires the cdo and nco modules to be loaded.
#
# USAGE
#    climatology <start_year> <end_year> <ifile> <ofile>
#
# EXAMPLE CDO COMMAND
#     cdo setdate,2085-01-01 -timmean -seldate,2075-01-01,2094-12-31 <infile> <ofile>
#
###################################################################################################

function usage {
    echo "USAGE: cdo_climatology.sh start_year end_year ifile ofile "
    echo "    start_year:  Year to start the aggregation "
    echo "    end_year:    Year to end the aggregation "
    echo "    ifile:       Input netcdf"
    echo "    ofile:       output netcdf file"
    exit 1
}

if [ 4 -eq $# ]; then
  year_start=$1
  year_end=$2
  ifile=$3
  ofile=$(readlink -f $4)
else
    usage
fi

#Check input
re='^[0-9]+$'
if ! [[ $year_start =~ $re ]] ; then
   echo "ERROR: year_start not a number" >&2; 
   exit 1
fi

if ! [[ $year_end =~ $re ]] ; then
   echo "ERROR: year_end not a number" >&2;
   exit 1
fi

which cdo > /dev/null 2>&1
if [ $? -ne 0 ] ; then
    echo "Can't find cdo executable"
    exit 1
fi

which ncatted > /dev/null 2>&1
if [ $? -ne 0 ] ; then
    echo "Can't find nco executable"
    exit 1
fi

#Set timepoint to middle of timeslice
(( year_mid = year_start + (year_end - year_start)/2 + 1))
cdo setdate,${year_mid}-01-01 -timmean -seldate,${year_start}-01-01,${year_end}-12-31 $ifile $ofile
ncatted -h -a climatology,time,a,c,"${year_start}-01-01, ${year_end}-12-31" ${ofile}

#Replace cell_methods of all variables
variable=`cdo showname ${ofile} | cut -f1 --delim='_' | sed 's/^[ ]//g'`
ncatted -h -a cell_methods,${variable}*,m,c,"time: mean over years" ${ofile}
