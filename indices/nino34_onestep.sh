#!/usr/bin/env bash
# This script takes in a number of monthly tos netCDF files
# and calculates the Nino3.4 index using cdo calls.
set -o errexit
set -o nounset

function usage() {
    echo Calculate Nino3.4 timeseries
    echo
    echo $0 infile_names [...] outfile_name
}

# Check command line args
if (( $# < 2 )) ; then
    usage
    exit 1
else
    outfilename="${@: -1}"
    length=$(($#-1))
    infilenames="${@:1:$length}"
fi

# Create tempfile, delete it on exit.
temp=$(mktemp -t nino_temp$$.XXXXXX.nc)
function cleanup() {
    rm "$temp"
}
trap cleanup EXIT

# Create the field averaged timeseries.
cdo -s -fldmean -sellonlatbox,-170,-120,5,-5 -mergetime "$infilenames" "$outfilename"

# Transform into an anomaly to calculate the index.
cdo -s -sub "$temp"  -timmean "$temp" "$outfilename"
