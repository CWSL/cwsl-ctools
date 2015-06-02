#!/usr/bin/env bash

##############################################################################
#
# Description: Aggregate data along the vertical axis
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
    echo "Aggregate data long the vertical axis."
    echo " "
    echo "USAGE: bash $0 method infile outfile"
    echo "   method:     Aggregation method."
    echo "               Choices: vertmin, vertmax, vertsum, vertmean, vertavg,"
    echo "                        vertvar, vertstd"
    echo "   infile:     Input file name"
    echo "   outfile:    Output file name"
    echo " "
    echo "   e.g. bash $0 vertmean indata.nc outdata.nc"
    exit 1
}

# Read the input arguments

if [ $# -eq 3 ] ; then
    method=$1
    infile=$2
    outfile=$3
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

# Execute the cdo function

cdo -O ${method} $infile $outfile

