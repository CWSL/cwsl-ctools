#!/usr/bin/env bash

##############################################################################
#
# Description: Simple arithmetic of two datasets.
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
    echo "Simple arthmetic of two datasets."
    echo " "
    echo "USAGE: bash $0 operation infile1 infile2 outfile"
    echo "   operation:  Arithmetic operation"
    echo "               Choices: add sub mul div min max atan2"
    echo "               For sub and div, it's (infile1 - infile2) or (infile1 / infile2)"
    echo "   infile1:    First input file" 
    echo "   infile2:    Second input file"
    echo "   outfile:    Output file name"

    echo "   e.g. bash $0 add indata1.nc indata2.nc outdata.nc"
    exit 1
}

function xmlcheck()  {
    infile=$1
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
    else
        infile=$infile
    fi
}

# Read the input arguments

if [ $# -eq 4 ] ; then
    operation=$1
    infile1=$2
    infile2=$3
    outfile=$4
else
    usage
fi

xmlcheck $infile1
infile1=$infile

xmlcheck $infile2
infile2=$infile


# Execute the cdo function
        
cdo -O ${operation} $infile1 $infile2 $outfile

