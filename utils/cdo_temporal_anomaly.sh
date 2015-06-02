#!/usr/bin/env bash

##############################################################################
#
# Description: Calculate the anomaly
#              
# Modules Required: cdo
#
# Authors:     Damien Irving
#
# Copyright:   2015 CSIRO
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
#############################################################################

function usage {
    echo "Temporal anomaly."
    echo " "
    echo "USAGE: bash $0 [-b clim_bounds] [-t timescale] infile outfile"
    echo "   clim_bounds:  Time bounds for the climatology used to calculate the anomaly timeseries." 
    echo "                   Format: YYYY-MM-DD,YYYY-MM-DD (no space before/after comma)"
    echo "                   Default: all timesteps are used"
    echo "   timescale:    Timescale for anomaly calculation"
    echo "                   Choices: yday, ymon, yseas (i.e. daily, monthly or seasonal anomaly)"
    echo "                   Default: temporal average across all timesteps is subtracted to calculate anomaly"
    echo "   infile:       Input file name"
    echo "   outfile:      Output file name"
    echo " "
    echo "   e.g. bash $0 indata.nc outdata.nc"
    echo "   e.g. bash $0 -t ymon indata.nc outdata.nc"
    echo "   e.g. bash $0 -b 1980-01-01,1999-12-31 -t yday indata.nc outdata.nc"
    exit 1
}


# Read the optional input arguments

subtractor=sub
averager=timmean
while getopts ":b:t:" opt; do
  case $opt in
    b)
      clim_bounds=$OPTARG
      ;;
    t)
      timescale=$OPTARG
      subtractor=${timescale}sub
      averager=${timescale}avg
      ;;
    \?)
      echo "Invalid option: -$OPTARG"
      exit 1
      ;;
    :)
      echo "Option -$OPTARG requires an argument."
      exit 1
      ;;
  esac
done

shift $((OPTIND-1))

# Read the required input arguments

if [ $# -ge 2 ] ; then
    infile=$1
    outfile=$2
else
    usage
fi

if [ ! -f $infile ] ; then
    echo "Input file doesn't exist: " $infile
    usage
fi


# Check if input is an XML file

temp_dir=$(mktemp -d)
function cleanup {
    rm -rf $temp_dir
}
trap cleanup EXIT

inbase=`basename $infile`
extn=`expr match "${inbase}" '.*\.\(.*\)'`
if [ $extn = 'xml' ] ; then
  tmp_in=${temp_dir}/xml_concat.$$.nc
  python ${CWSL_CTOOLS}/utils/xml_to_nc.py None $infile $tmp_in
  infile=$tmp_in
fi

# Get the climatology file

if [ -z "${clim_bounds}" ]; then 
    clim_file=$infile 
else 
    clim_file="-seldate,${clim_bounds} $infile" 
fi

# Calculate the anomaly

cdo -O ${subtractor} $infile -${averager} ${clim_file} $outfile

