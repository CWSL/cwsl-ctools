#!/usr/bin/env bash
set -o nounset
set -o errexit

##############################################################################
#
# Description: Calculate the Niño 3.4 index from an
#              input netCDF monthly time series.
#
# Modules Required: cct, cdo
#
# Authors:     Tim Bedin
#              Michael Grose
#
# Copyright:   2014 CSIRO
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

temp_dir=$(mktemp -d)
function cleanup {
    rm -rf $temp_dir
}
trap cleanup EXIT

usage () {
    echo "Calculate the Nino3.4 index from an input sst file."
    echo "$0 infile outfile startdate enddate"
    echo
    echo "Outputs a monthly time series of NINO3.4 index between dates specified"
    echo "using a 30 year rolling climatology to calculate the sea surface temperature"
    echo "anomaly."
    echo
    echo "Requires the cawcr cct and cdo modules."
}

# Checks inputs are correct
if [ $# -lt 4 ]; then
    usage
    exit 1
fi

sstfile=$1
outputfile=$2
startdate=$3
enddate=$4

# Define tempfile locations.
tempinput=$temp_dir/restrictedtime.$$.nc
temp1=$temp_dir/clim_temp.$$.nc
temp2=$temp_dir/time_series_temp.$$.nc

# restrict input to required year dates
cdo seldate,$startdate"-1-1",$enddate"-31-12" $sstfile $tempinput

# Check years present in the input file
years=$(cdo showyear ${tempinput})

# isolate the decades in the source file, make an array of the decades
IFS=' ' read -a yeararray <<< "$years"

decades=""
for year in "${yeararray[@]}"; do
    if [ $(( ${year} % 10 )) -eq 0 ]; then
        decades="$decades $year"
    fi
done

IFS=' ' read -a decadearray <<< "$decades"
num_decades=${#decadearray[@]}
if [[ "$num_decades" -lt "4" ]]; then
    echo "ERROR: Rolling climatology requires at least 4 decades to calculate climatology"
    exit 1
fi

# Calculate climatology and anomalies for first decade, using first 3 decades as climatology
cyr1=$((${decadearray[0]}+1))
cyr2=$((${decadearray[0]}+30))
year1=$((cyr1-1))
year2=$((cyr1+8))
echo "cyr1 = $cyr1 cyr2 = $cyr2 year1 = $year1 year2 = $year2"
cdo ymonmean -seldate,$cyr1"-1-1",$cyr2"-31-12" $tempinput $temp1
cdo ymonsub -seldate,$year1"-1-1",$year2"-31-12" $tempinput $temp1 $temp2
cdo fldavg -sellonlatbox,190,240,-5,5 $temp2 $temp_dir/temp_$$_n34_${year1}-${year2}.nc

# loop through all decades except 1 and last two, make anomaly then calculate NINO3.4 index
for dcd in "${decadearray[@]:1:$((num_decades - 3))}"; do
    cyr1=$((dcd-9))
    cyr2=$((dcd+20))
    year1=$dcd
    year2=$((dcd+9))
    echo "cyr1 = $cyr1 cyr2 = $cyr2 year1 = $year1 year2 = $year2"
    cdo ymonmean -seldate,$cyr1"-1-1",$cyr2"-31-12" $tempinput $temp1
    cdo ymonsub -seldate,$year1"-1-1",$year2"-31-12" $tempinput $temp1 $temp2
    # Calculate NINO3.4
    cdo fldavg -sellonlatbox,190,240,-5,5 $temp2 $temp_dir/temp_$$_n34_${year1}-${year2}.nc
done

# Calculate climatology and anomalies for second last decade, using last 3 decades as climatology
echo These things are in the array:
for decade in "${decadearray[@]}" ; do
    echo "This decade: $decade"
done

cyr1=$((${decadearray[num_decades-4]}+1))
cyr2=$((${decadearray[num_decades-1]}))
cdo ymonmean -seldate,$cyr1"-1-1",$cyr2"-31-12" $tempinput $temp1
year1=$((cyr2-10))
year2=$((cyr2-1))
echo "cyr1 = $cyr1 cyr2 = $cyr2 year1 = $year1 year2 = $year2"
cdo ymonsub -seldate,$year1"-1-1",$year2"-31-12" $tempinput $temp1 $temp2
# Calculate NINO3.4
cdo fldavg -sellonlatbox,190,240,-5,5 $temp2 $temp_dir/temp_$$_n34_${year1}-${year2}.nc

# Put all NINO3.4 files together and save to output file
cdo -O mergetime $temp_dir/temp_$$_n34_????-????.nc $outputfile

# Check time parameters
yearin=$(cdo showyear $tempinput)
yearout=$(cdo showyear $outputfile)
echo "years in = $yearin years out= $yearout"

echo Output file name is "$outputfile"