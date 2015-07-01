#!/usr/bin/env bash

##############################################################################
#
# Description: Calculates a histogram
#              
# Modules Required: cdo
#
# Authors:     Craig Heady
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
    echo "Calculates a histogram"
    echo " "
    echo "USAGE: bash $0 method, infile outfile"
    echo "   method:     Histogram method."
    echo "               Choices: histcount, histsum, histmean, histfreq."
    echo "   bin_list:   Comma seprated list of bin values."
    echo "               eg temperature   -inf,-40,-30,-20,-10,0,10,20,30,40,inf"
    echo "               eg precipitation 0,20,40,60,80,100,150,200,300,400,inf"
    echo "   infile:     Input file name"
    echo "   outfile:    Output file name"
    echo " "
    echo "   e.g. bash $0 histcount,bin_list indata.nc outdata.nc"
    exit 1
}


# Read the input arguments

if [ $# -eq 3 ] ; then
    options=$1
    infile=$2
    outfile=$3
else
    usage
fi

if [ ! -f $infile ] ; then
    echo "Input file doesn't exist: " $infile
    usage
fi

# Execute the cdo function

cdo -O $options $infile $outfile

