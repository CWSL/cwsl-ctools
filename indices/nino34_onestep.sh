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

# Create required tempfiles, delete on exit.
time_temp=$(mktemp -t nino_timetemp$$.XXXXXX.nc)
merged_temp=$(mktemp -t nino_mergetemp$$.XXXXXX.nc)
anomaly_temp=$(mktemp -t nino_anomalytemp$$.XXXXXX.nc)
function cleanup() {
    rm "$merged_temp" "$anomaly_temp" "$time_temp"
}
trap cleanup EXIT

# If infilenames contains spaces then must be more than one file.
if [[ $infilenames == *" "* ]] ; then
    cdo -s mergetime ${infilenames} ${merged_temp}
    cdo -s -r -fldmean -sellonlatbox,190,240,-5,5 -selyear,1900/2100 ${merged_temp} ${time_temp}
else
    cdo -s -r -fldmean -sellonlatbox,190,240,-5,5 -selyear,1900/2100 ${infilenames} ${time_temp}
fi

# Calculate and subtract monthly climatology to make anomaly time series
cdo -s -r -ymonsub ${time_temp} -ymonmean ${time_temp} ${anomaly_temp}

# Detrend and take the field mean over the Nino3.4 box.
cdo -s detrend ${anomaly_temp} ${outfilename}
