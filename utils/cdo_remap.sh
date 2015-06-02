#!/usr/bin/env bash

##############################################################################
#
# Description: Remap to new horizontal grid.
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
    echo "Remap to new horizontal grid."
    echo " "
    echo "USAGE: bash $0 method grid infile outfile"
    echo "   method:     Method for remapping to new horizontal grid"
    echo "               Choices: remapbil, remapbic, remapdis, remapnn, remapcon, remapcon2, remaplaf"
    echo "               If in doubt, use remapcon2"
    echo "   grid:       Name of cdo target grid or interpolation weights file. Grid names are at: " 
    echo "               https://code.zmaw.de/projects/cdo/embedded/index.html#x1-150001.3.2  "
    echo "   infile:     Input file name"
    echo "   outfile:    Output file name"

    echo "   e.g. bash $0 remapcon2 r360x180 indata.nc outdata.nc"
    exit 1
}


# Read the input arguments

if [ $# -eq 4 ] ; then
    method=$1
    gridname=$2
    infile=$3
    outfile=$4
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

# Process gridname

echo $gridname
case $gridname in
    r*x* )
      cdogrid=$gridname
      ;;
    lon*_lat* )
      cdogrid=$gridname
      ;;
    t*grid )
      cdogrid=$gridname
      ;;
    gme* )
      cdogrid=$gridname
      ;;
    * )
      if [ -f $gridname ] ; then  # TODO: Could add an extra option here to a directory of saved grid files
        cdogrid=$gridname
      else
        echo "Can't recognise or find grid definition: " $gridname
        exit 1
      fi
esac

# Execute the cdo function
cdo -O ${method},$cdogrid $infile $outfile

