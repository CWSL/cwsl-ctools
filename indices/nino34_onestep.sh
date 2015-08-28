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
offset_temp=$(mktemp -t nino_offsettemp$$.XXXXXX.nc)
slope_temp=$(mktemp -t nino_slopetemp$$.XXXXXX.nc)
detrended_temp=$(mktemp -t nino_detrendedtemp$$.XXXXXX.nc)
detrended_anomaly_temp=$(mktemp -t nino_detrendedanomalytemp$$.XXXXXX.nc)
function cleanup() {
    rm "$merged_temp" "$anomaly_temp" "$offset_temp" "$slope_temp"  "$detrended_temp" "$detrended_anomaly_temp" "$time_temp"
}
trap cleanup EXIT

# Merge the timeseries, then select the correct dates.
cdo -s -r -mergetime ${infilenames} ${merged_temp}
cdo -s -r -selyear,1900/2100 ${merged_temp} ${time_temp}

# Calculate and subtract monthly climatology to make anomaly time series
cdo -s -r -ymonsub ${merged_temp} -ymonmean ${time_temp} ${anomaly_temp}

# Subtract the linear trend, but keep the offset.
cdo -s -r trend ${anomaly_temp} ${offset_temp} ${slope_temp}
cdo -s -r detrend ${anomaly_temp} ${detrended_temp}
cdo -s add ${detrended_temp} ${offset_temp} ${detrended_anomaly_temp}

# Detrend and take the field mean over the Nino3.4 box.
cdo -s -fldmean -sellonlatbox,190,240,-5,5 ${detrended_anomaly_temp} ${outfilename}
