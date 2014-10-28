#!/usr/bin/env bash
#
# Author: David Kent (David.Kent@csiro.au)
#         Tim Bedin (small sum/mean modification 2013, added altering the variables in place) (Tim.Bedin@csiro.au)
#                   (stopped writing large files to JOBFS - 29/04/2013)
# Date:   3/05/2011
#
#
# Copyright 2011/2013, CSIRO
#

version='$Revision: 1439 $'

####################################
###  START FUNCTION DEFINITIONS  ###

function usage {
    echo "USAGE: seas_vars.sh -a|(vname newvname) [-g gfile] start_year end_year seas_agg ifile ofile "
    echo "    -a:          Process all variables in the file "
    echo "    -g:          grid netcdf file (optional)"
    echo "    vname:       Original input variable name "
    echo "    newvname:    Variable name for output file "
    echo "    start_year:  Year to start the aggregation "
    echo "    end_year:    Year to end the aggregation "
    echo "    seas_agg:    The aggregation type to perform (can be one of: seasavg, seassum, seasmax, seasmin)"
    echo "    ifile:       Input netcdf or cdat xml file"
    echo "    ofile:       output netcdf file"
    exit 1
}

function convert_input {
    # Function to check the extension of the input file and convert
    # it to a netCDF if necessary.
    # Function takes no arguments.
    inbase=`basename $in`
    extn=`expr match "${inbase}" '.*\.\(.*\)'`
    if [ $extn = 'xml' ] ; then
	tmp_in=$SMALLTMP/xml_concat.$$.nc
	python ${CWSL_CTOOLS}/utils/xml_to_nc.py None $in $tmp_in -s $start_year -e $end_year
	in=$tmp_in
    fi
    
    if [ ! -f $in ] ; then
        echo "Conversion of file from XML catalogue failed."
        exit 1
    fi
}

function check_size {
    ####CHECK FOR FILESIZE LARGER THAN JOBFS######
    # Check the size of the input file - if it is big, we
    # need to use /short rather than jobfs for our large files.
    # Function takes no arguments.
    
    filesize=`python ${CWSL_CTOOLS}/utils/file_size.py $in`
    
    if [ "${filesize}" -gt "2147483648" ];
    then
	new_directory="/short/${PROJECT}/${USER}"
	mkdir -p $new_directory
	BIGTMP=${new_directory}
    else
	BIGTMP=$TMPDIR
    fi
    
    # We need two temp file locations - a place to
    # write the large files and a place to put the
    # small, temporary files.
    # We always use jobfs for small files.
    SMALLTMP=$TMPDIR
    
    echo "Using BIGTMP $BIGTMP"
    echo "Using SMALLTMP $SMALLTMP"
}
    
###  END FUNCTION DEFINITIONS  ###
##################################

all=1
while getopts ":ag:" opt;
do
    case $opt in
	a)
	    all=0
	    ;;
	g)
	    grid=$OPTARG
	    ;;
	\?)
	    echo "Invalid option: -$OPTARG" >&2
	    ;;
    esac
done

shift $((OPTIND-1))

if [ ${all} -eq 0 ] ; then
  start_year=$1
  end_year=$2
  seas_agg=$3
  in=$4
  out=$(readlink -f $5)
  vars=`cdo showname $in`

elif [ 7 -eq $# ]; then
  vars=$1
  varorigout=$2
  start_year=$3
  end_year=$4
  seas_agg=$5
  in=$6
  out=$(readlink -f $7)

else
  usage
fi

which cdo > /dev/null 2>&1
if [ $? -ne 0 ] ; then
    echo "Can't find cdo executable"
    exit 1
fi
which ncatted > /dev/null 2>&1
if [ $? -ne 0 ] ; then
    echo "Can't find ncatted executable"
    exit 1
fi

if [ ! -f $in ] ; then
    echo "Input file doesn't exist: " $in
    exit 1
fi

if [ $grid ] && [ ! -f $grid ] ; then
   echo "Gridfile does not exist. Exiting: " $grid
   exit 1
fi

#Check file size and convert xml catalogue files
check_size
convert_input

# Now check the seas_agg and set the summean aggregation type
# daysinmonth is a flag for multiplying the value by the
# number of days in the month - useful for moisture variables such as pr.
daysinmonth=0
case $seas_agg in
    seasavg)
	summean=mean ;;
    seassum)
	summean=sum
	daysinmonth=1 ;;
    seasmax)
	summean=max ;;
    seasmin)
	summean=min ;;
    \?)
	echo "Unrecognised seas_agg: " $seas_agg
	exit 1
	;;
esac

# If output exists remove it, as if it is corrupted will
# cause problems when merging in data!
if [ -e ${out} ]; then
    rm ${out}
fi

# Check that we start in Jan and end in November or Dec
# as we throw away the last december anyway!
monstart=`cdo showmon $in | awk '{print $1 }'`
monend=`cdo showmon $in | awk '{print $NF }'`
if [ $monstart -ne 1 -o \( $monend -ne 12 -a $monend -ne 11 \) ] ; then
  if [ $monstart -ne 1 ] ; then
    yrstart=`cdo showyear $in | awk '{ print $2 }'`
  else
    yrstart=`cdo showyear $in | awk '{ print $1 }'`
  fi

  if [ $monend -ne 12 ] && [ $monend -ne 11 ] ; then
    yrend=`cdo showyear $in | awk '{ print $(NF-1) }'`
  else
    yrend=`cdo showyear $in | awk '{ print $NF }'`
  fi
  tmp_in2=$SMALLTMP/strip_months.$$.nc
  echo "There are extra months at the start or end. Stripping..."
  cdo seldate,${yrstart}-1-1,${yrend}-12-31 $in $tmp_in2
  in=$tmp_in2
fi

if [ ! -f $in ] ; then
    echo "Stripping extra months failed."
    exit 1
fi

###########################
#Check grid type 29/06/2012
###########################

if [ $grid ] ; then

  regrid=false

  #Some files contain more than one grid!
  grid_type=`cdo griddes $in | grep 'gridtype' | awk '{ print $3 }'`
  for g in ${grid_type}; do
    if [ $g = 'curvilinear' ]; then
      regrid=true
    fi
  done

  #Regrid
  if [ $regrid ] ; then
    echo "Regridding"
    tmp_remap=$SMALLTMP/grid.$$.nc
    #Remap to landsea (or other grid)
    cdo remapbil,$grid $in $tmp_remap
    in=$tmp_remap
  fi
fi

####END CHECK GRID########

# If $daysinmonth equals 1, multiply the
# input variable by the number of days in the month.
if [ ${daysinmonth} -eq 1 ] ; then
  tmp1_in=$tmp_in
  tmp_in=$SMALLTMP/daysin_mon.$$.nc
  cdo muldpm $in $tmp_in
  in=$tmp_in
fi

echo "Variables to be processed:"
echo $vars
for var in $vars ; do

  if [ -n "${varorigout}" ] ; then
      varout=$varorigout
  else
      varout=$var
  fi

  variable_storage=$SMALLTMP/temp_merged_file.$$.$var.nc
  merged_file=$BIGTMP/merged_file.$$.$var.nc
  fixed_time=$BIGTMP/fixed_time.$$.$var.nc
  temp_out=$BIGTMP/tmp_out.$$.$var.nc

  # Ensure we have a real, normalised file rather than a symlink or a relative
  # path
  in=`readlink -f $in`

  # Get the mean annual and save in a temp file.
  # All other variables will be appended to this file.
  cdo chname,$var,${varout}_annual -year${summean} -selname,$var $in ${merged_file}
  ncatted -h -a cell_methods,${varout}_annual,m,c,"time: ${summean} within years" ${merged_file}
  ncatted -h -a long_name,${varout}_annual,a,c," (annual)" ${merged_file}

  # Get the mean for each standard season
  firstmon=`cdo showmon -seltimestep,1 $in`

  # Create the djf temporary files.
  djf_file_1=$SMALLTMP/djf_1_$$.nc
  djf_file_2=$SMALLTMP/djf_2_$$.nc
  djf_file_3=$SMALLTMP/djf_3_$$.nc
  djf_file_4=$SMALLTMP/djf_4_$$.nc

  ## Select first year's jan and feb (then set to missing anyway....)
  cdo chname,$var,${varout}_djf -tim${summean} -seltimestep,0,1 -selname,$var $in $djf_file_1
  cdo setrtomiss,-1e36,1e36 $djf_file_1 $djf_file_2

  #DJF, skip is first 11 months
  t0=`expr 11 - $firstmon + 1`
  cdo chname,$var,${varout}_djf -timsel${summean},3,$t0,9 -selname,$var $in $djf_file_3
  nyrs=`cdo ntime $djf_file_3`
  endyr=`expr ${nyrs} - 2`
  # Keep all but last (the single december)
  monend=`cdo showmon $in | awk '{print $NF }'`
  if [ $monend -eq 12 ] ; then
      ncks -dtime,0,$endyr $djf_file_3 $djf_file_4
      rm $djf_file_3
  else
      mv $djf_file_3 $djf_file_4
  fi

  # DJF concat missing value for first year then chop off last year's december
  cdo mergetime $djf_file_2 $djf_file_4 ${variable_storage}
  ncatted -h -a cell_methods,${varout}_djf,m,c,"time: ${summean} within years" ${variable_storage}
  ncatted -h -a long_name,${varout}_djf,a,c," (djf)" ${variable_storage}
  rm $djf_file_1 $djf_file_2 $djf_file_4

  # Add djf to the merged file.
  ncks -h -A -v ${varout}_djf ${variable_storage} ${merged_file}
  # Delete the variable storage.
  rm ${variable_storage}

  #MAM, skip is first 2 months
  t0=`expr 2 - $firstmon + 1`
  cdo chname,$var,${varout}_mam -timsel${summean},3,$t0,9 -selname,$var $in ${variable_storage}
  ncatted -h -a cell_methods,${varout}_mam,m,c,"time: ${summean} within years" ${variable_storage}
  ncatted -h -a long_name,${varout}_mam,a,c," (mam)" ${variable_storage}

  # Add mam to the merged file.
  ncks -h -A -v ${varout}_mam ${variable_storage} ${merged_file}
  # Delete the variable storage.
  rm ${variable_storage}

  #JJA, skip is first 5 months
  t0=`expr 5 - $firstmon + 1`
  cdo chname,$var,${varout}_jja -timsel${summean},3,$t0,9 -selname,$var $in ${variable_storage}
  ncatted -h -a cell_methods,${varout}_jja,m,c,"time: ${summean} within years" ${variable_storage}
  ncatted -h -a long_name,${varout}_jja,a,c," (jja)" ${variable_storage}

  # Add jja to the merged file.
  ncks -h -A -v ${varout}_jja ${variable_storage} ${merged_file}
  # Delete the variable storage.
  rm ${variable_storage}

  #SON, skip is first 8 months
  t0=`expr 8 - $firstmon + 1`
  cdo chname,$var,${varout}_son -timsel${summean},3,$t0,9 -selname,$var $in ${variable_storage}
  ncatted -h -a cell_methods,${varout}_son,m,c,"time: ${summean} within years" ${variable_storage}
  ncatted -h -a long_name,${varout}_son,a,c," (son)" ${variable_storage}

  # Add son to the merged file.
  ncks -h -A -v ${varout}_son ${variable_storage} ${merged_file}
  # Delete the variable storage.
  rm ${variable_storage}

  #NDJFMA, skip is first 10 months
  # Create the ndjfma temporary files.
  ndjfma_file_1=$SMALLTMP/ndjfma_1_$$.nc
  ndjfma_file_2=$SMALLTMP/ndjfma_2_$$.nc
  ndjfma_file_3=$SMALLTMP/ndjfma_3_$$.n
  ndjfma_file_4=$SMALLTMP/ndjfma_4_$$.nc

  ## Select first year's jan - april (then set to missing anyway....)
  cdo chname,$var,${varout}_ndjfma -tim${summean} -seltimestep,1,2,3,4 -selname,$var $in $ndjfma_file_1
  cdo setrtomiss,-1e36,1e36 $ndjfma_file_1 $ndjfma_file_2
  t0=`expr 10 - $firstmon + 1`
  cdo chname,$var,${varout}_ndjfma -timsel${summean},6,$t0,6 -selname,$var $in $ndjfma_file_3
  nyrs=`cdo ntime $ndjfma_file_3`
  endyr=`expr ${nyrs} - 2`
  # Keep all but last (the november/december)
  ncks -dtime,0,$endyr $ndjfma_file_3 $ndjfma_file_4

  # NDJFMA concat missing value for first year then chop off
  # last year's december
  cdo mergetime $ndjfma_file_2 $ndjfma_file_4 ${variable_storage}
  ncatted -h -a cell_methods,${varout}_ndjfma,m,c,"time: ${summean} within years" ${variable_storage}
  ncatted -h -a long_name,${varout}_ndjfma,a,c," (ndjfma)" ${variable_storage}
  rm $ndjfma_file_1 $ndjfma_file_2 $ndjfma_file_3 $ndjfma_file_4

  # Add ndjfma to the merged file.
  ncks -h -A -v ${varout}_ndjfma ${variable_storage} ${merged_file}
  # Delete the variable storage.
  rm ${variable_storage}

  #MJJASO, skip is first 4 months
  t0=`expr 4 - $firstmon + 1`
  cdo chname,$var,${varout}_mjjaso -timsel${summean},6,$t0,6 -selname,$var $in ${variable_storage}
  ncatted -h -a cell_methods,${varout}_mjjaso,m,c,"time: ${summean} within years" ${variable_storage}
  ncatted -h -a long_name,${varout}_mjjaso,a,c," (mjjaso)" ${variable_storage}

  # Add mjjaso to the merged file.
  ncks -h -A -v ${varout}_mjjaso ${variable_storage} ${merged_file}
  # Delete the variable storage.
  rm ${variable_storage}

  # For each month, select out the appropriate month and then add it to
  # the merged file.
  months=(january february march april may june july august september october november december)

  i=0
  for month in "${months[@]}"; do
      i=`expr $i + 1`
      #If month December and data selection ends in November mask last time point
      if [ $i -eq 12 ] && [ $monend -eq 11 ] ; then
          cdo chname,$var,${varout}_${month} -selmon,$i -selname,$var $in $djf_file_1
          #Grab a single time point and set date to december of last year
          cdo chname,$var,${varout}_${month} -seltimestep,1 -selname,$var $in $djf_file_2
          yrend=`cdo showyear $in | awk '{ print $NF }'`
          dayofmonth=`cdo showdate $in | awk '{split($NF,date,"-"); print date[2]}'`
          cdo setdate,${yrend}-${i}-${dayofmonth} $djf_file_2 $djf_file_3
          cdo setrtomiss,-1e36,1e36 $djf_file_3 $djf_file_4
          # DJF concat missing value for first year then chop off last year's december
          cdo mergetime $djf_file_1 $djf_file_4 ${variable_storage}
          rm $djf_file_1 $djf_file_2 $djf_file_3 $djf_file_4
      else
          cdo chname,$var,${varout}_${month} -selmon,$i -selname,$var $in ${variable_storage}
      fi

      # Append this month to the merged file.
      ncks -h -A -v ${varout}_${month} ${variable_storage} ${merged_file}
      ncatted -h -a long_name,${varout}_${month},a,c," ${month}" ${merged_file}
      # Delete the variable storage.
      rm ${variable_storage}
  done
  
  # If the output file exists, merge the merged file 
  # with the output and copy it to a temp location.
  # Otherwise, just copy it to the temporary location.
  if [ -e ${out} ]; then
      cdo merge ${merged_file} ${out} ${temp_out}
  else
      cp ${merged_file} ${temp_out}
  fi
  # Now copy the temporary output file
  # to the output file.
  cp ${temp_out} ${out}
   
done
# End of variable loop.

# Fix the time axis of this file - set it to a yearly
# time axis.
first_year=$(cdo showyear -seltimestep,1 $merged_file)
# Strip any whitespace from first_year
first_year="${first_year//[[:space:]]/}"

cdo settaxis,${first_year}-01-01,12:00:00,1year $out $fixed_time
cdo setcalendar,standard ${fixed_time} $out

ncatted -h -a script_version,global,a,c,"Calculated by $0 version $version" $out

# If we have a mean, change the units.
if [ "$summmean" = "sum" ]; then
    # Change units on the output file if we have calculated the sum.
    ncatted -a units,,a,c," days" $out
fi

# Clean up.
if [ -f $variable_storage ]
then
    rm -rf $variable_storage
fi

if [ -f $merged_file ]
then
    rm -rf $merged_file
fi

if [ -f $tmp_remap ]
then
    rm -rf $tmp_remap
fi

if [ -f $tmp_in ]
then
    rm -rf $tmp_in
fi

if [ -f $tmp_in2 ]
then
     rm -rf $tmp_in2
fi

if [ -f $tmp1_in ]
then
    rm -rf $tmp1_in
fi

if [ -f $fixed_time ] 
then
    rm -rf $fixed_time
fi

if [ -f $time_restricted ]
then
    rm -rf $time_restricted
fi

if [ -f $temp_out ] 
then
    rm -rf $temp_out
fi
