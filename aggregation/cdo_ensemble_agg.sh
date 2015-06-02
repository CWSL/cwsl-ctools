#!/usr/bin/env bash

##############################################################################
#
# Description: Calculate an ensemble statistic
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
    echo "Calculate an ensemble statistic"
    echo " "
    echo "USAGE: bash $0 statistic infile1 infile2 ... infileN outfile"
    echo "   statistic:  Choices: ensmin, ensmax, enssum, ensmean, ensavg,"
    echo "                        ensvar, ensvar1, ensstd, ensstd1," 
    echo "                        enspctl,P (where P is the percentile)"
    echo "   infile:     Input file name"
    echo "   outfile:    Output file name"
    echo " "
    echo "   e.g. bash $0 ensmean indata1.nc indata2.nc indata3.nc outdata.nc"
    echo "   e.g. bash $0 enspctl,90 indata1.nc indata2.nc indata3.nc indata4.nc outdata.nc"
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

    inbase=$(basename $infile)
    extn=$(expr match "${inbase}" '.*\.\(.*\)')
    if [ $extn = 'xml' ] ; then
        tmp_in=${temp_dir}/xml_concat.$$.nc
        python ${CWSL_CTOOLS}/utils/xml_to_nc.py None $infile $tmp_in 
        infile=$tmp_in
    else
        infile=$infile
    fi
}


# Read the input arguments

if [ $# -ge 4 ] ; then
    inargs=( "$@" )
    statistic=${inargs[0]}
    infiles=${inargs[@]:1:$(expr $# - 2)}
    outfile=${inargs[@]: -1}
else
    usage
fi

checked_infiles=()
for file in ${infiles[@]} ; do
    xmlcheck $file
    checked_infiles+=("$infile")
done

# Execute the cdo function

cdo -O ${statistic} ${checked_infiles[@]} $outfile
