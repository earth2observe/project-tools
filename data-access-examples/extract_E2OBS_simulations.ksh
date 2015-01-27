#! /bin/ksh
# Kornshell Script to E2OBS simulations
# Download from the Threads server: http://wci.earth2observe.eu/thredds
# Provider ECMWF 
# requires:
#      wget 
#      nco 

## for command line options:
# ./extract_E2OBS_simulations.ksh --man 

# DESCRIPTION
#    Script to extract e2obs model simulations.
# 
# SYNOPSIS
#   ./extract_E2OBS_simulations.ksh [ options ]
# 
#  Returns
#  0 if no errors found. -9 if remote file is not found. Any other in case of error.
# 
#  Output
#     Output files saved to datadir/Cid/Cver/
# 
#  External
#     Requires wget and nco
# 
# OPTIONS
#   -i, --id=id     Institution identification. Allowed values: ecmwf,univu,metfr,nerc,jrc,cnrs,univk,ambio,csiro,eth. The default value is NONE.
#   -v, --variable=var
#                   Variable name. The default value is NONE.
#   -d, --domain=domain
#                   Domain. The default value is glob30.
#   -e, --experiment=ver
#                   Experiment name. The default value is wrr1.
#   -f, --frequency=frequency
#                   Frequency. Allowed values: mon,day,1hr,fix. The default value is day.
#   -a, --ystart=ystart
#                   Start year of simulation. The default value is 1979.
#   -b, --yend=yend End year of simulation. The default value is 2012.
#   -l, --datadir=datadir
#                   Base data directory. Temporary files saved to: datadir/tmp/; Output files saved to datadir/Cid/Cver/ . The default value is ./.
#   -m, --plat=Plat Latitude of point to extract. The default value is -999.
#   -n, --plon=Plon Longitude of point to extract The default value is -999.
#   -p, --rname=Creg
#                   region or point tag name The default value is NONE.
#   -q, --latmin=latmin
#                   Latitude South bound The default value is -999.
#   -r, --latmax=latmax
#                   Latitude North bound The default value is -999.
#   -s, --lonmin=lonmin
#                   Longitude West bound The default value is -999.
#   -t, --lonmax=lonmax
#                   Longitude East bound The default value is -999.
#   -u, --dstart=dstart
#                   Date start to cut (any format understood by date) The default value is -999.
#   -g, --dend=dend Date end to cut (any format understood by date) The default value is -999.
#   -w               be verbose (add set -x)
#   -y               if used, the temporary file will not be removed
#   -c               Only check if remove file exists (if remote file exists returns 0, otherwise -9
# 
# IMPLEMENTATION
#   author          Emanuel Dutra <emanuel.dutra@ecmwf.int>




# Script setup---------------------------------------------
set -eu 

## defaults
httpLOC="https://wci.earth2observe.eu/thredds/fileServer/"
dapLOC="https://wci.earth2observe.eu/thredds/dodsC/"


## defaults, changed via command line 
Cid="NONE"    # institution identifier
Cvar="NONE"   # variable to download/process 
Cver="wrr1"   # experiment name
Cdomain="glob30" # domain 
Cfreq="day"   # frequency 
Cystart=1979  # start year of simulations
Cyend=2012    # end year of simulations
verbose=false  # if true script is verbose
Lcheck_remote=false  # if true only check if remote file exists 
datadir="./"      # base location for the data
Lclean=true       # if true remove temporary file on exit
Creg="NONE"       # when extracting only a point or region this will be the tag name 
Plat=-999         # Latiude of point to extract
Plon=-999         # Longitude of point to extract
latmin=-999       # latitude south box 
latmax=-999       # latitude north box 
lonmin=-999       # longitude west box 
lonmax=-999       # longitude east box 
dstart=-999       # date start yyyymmmdd
dend=-999         # date end yyyymmdd

USAGE=""
USAGE+="[-author?Emanuel Dutra <emanuel.dutra@ecmwf.int>]"
USAGE+="[+DESCRIPTION? Script to extract e2obs model simulations.]" 
USAGE+="[+ Returns?] {[ 0 if no errors found. -9 if remote file is not found. Any other in case of error.]}"
USAGE+="[+ Output?] {[Output files saved to datadir/Cid/Cver/]}"
USAGE+="[+ External?] {[Requires wget and nco]}"
USAGE+="[i:id]:[id:=${Cid}?Institution identification. Allowed values: ecmwf,univu,metfr,nerc,jrc,cnrs,univk,ambio,csiro,eth.]"
USAGE+="[v:variable]:[var:=${Cvar}?Variable name.]"
USAGE+="[d:domain]:[domain:=${Cdomain}?Domain. ]"
USAGE+="[e:experiment]:[ver:=${Cver}?Experiment name.]"
USAGE+="[f:frequency]:[frequency:=${Cfreq}?Frequency. Allowed values: mon,day,1hr,fix. ]"
USAGE+="[a:ystart]#[ystart:=${Cystart}?Start year of simulation.]"
USAGE+="[b:yend]#[yend:=${Cyend}?End year of simulation.]"
USAGE+="[l:datadir]:[datadir:=${datadir}?Base data directory. Temporary files saved to: datadir/tmp/; Output files saved to datadir/Cid/Cver/ . ]"
USAGE+="[m:plat]:[Plat:=${Plat}?Latitude of point to extract.]"
USAGE+="[n:plon]:[Plon:=${Plon}?Longitude of point to extract]"
USAGE+="[p:rname]:[Creg:=${Creg}?region or point tag name]"
USAGE+="[q:latmin]:[latmin:=${latmin}?Latitude South bound]"
USAGE+="[r:latmax]:[latmax:=${latmax}?Latitude North bound]"
USAGE+="[s:lonmin]:[lonmin:=${lonmin}?Longitude West bound]"
USAGE+="[t:lonmax]:[lonmax:=${lonmax}?Longitude East bound]"
USAGE+="[u:dstart]:[dstart:=${dstart}?Date start to cut (any format understood by date)]"
USAGE+="[g:dend]:[dend:=${dend}?Date end to cut (any format understood by date)]"
USAGE+="[w? be verbose (add set -x) ]"
USAGE+="[y? if used, the temporary file will not be removed  ]"
USAGE+="[c? Only check if remove file exists (if remote file exists returns 0, otherwise -9  ]"

while getopts "$USAGE" optchar ; do
    case $optchar in
    a) Cystart=${OPTARG} ;;
    b) Cyend=${OPTARG} ;;  
    c) Lcheck_remote=true ;;
    d) Cdomain=${OPTARG} ;;
    e) Cver=${OPTARG} ;;
    f) Cfreq=${OPTARG} ;;
    i) Cid=${OPTARG} ;;
    l) datadir=${OPTARG} ;;  
    y) Lclean=false ;; 
    m) Plat=${OPTARG} ;;  
    n) Plon=${OPTARG} ;;  
    p) Creg=${OPTARG} ;;  
    v) Cvar=${OPTARG} ;;
    w) verbose=true ;; 
    y) Lclean=false ;;  
    q) latmin=${OPTARG} ;;
    r) latmax=${OPTARG} ;;
    s) lonmin=${OPTARG} ;;
    t) lonmax=${OPTARG} ;;
    u) dstart=${OPTARG} ;;
    g) dend=${OPTARG} ;;
    esac
done

## generate file name and locations

if [[ $verbose = true ]] ; then 
  set -x
fi

## file name generation 

if [[ $Cfreq = "fix" ]]; then  # special case for fix fields
  file_in="e2o_${Cid}_${Cver}_${Cdomain}_${Cfreq}_${Cvar}.nc"
else
  file_in="e2o_${Cid}_${Cver}_${Cdomain}_${Cfreq}_${Cvar}_${Cystart}-${Cyend}.nc"
fi
file_path="${Cid}/${Cver}"
http_path=$httpLOC/${file_path}/
dap_path=$dapLOC/${file_path}/
local_path=${datadir}/$file_path/
temp_path=${datadir}/tmp/

# special case of univu data location on the server
if [[ $Cid = univu ]]; then
  http_path=$httpLOC/uu/wrr1/
fi



## In case we only want to know if the file exists 
if [[ $Lcheck_remote = true ]]; then
  wget -q --spider $http_path/${file_in} && LrExist=true || LrExist=false 
  if [[ $LrExist = true ]]; then
    echo "fileurl: $http_path/${file_in} exist"
    echo "opendap: $dap_path/${file_in}.html exist"
    exit 0
  else
    echo "File: $http_path/${file_in} does not exist"
    exit -9
  fi
fi

echo "Input file: $file_in"
echo "http_path $http_path"
echo "local_path $local_path"
echo "temp_path $temp_path"

## check if file exists locally:
LlExist=false
LtExist=false
if [[ -r $local_path/${file_in} ]]; then
  LlExist=true
fi
if [[ -r $temp_path/${file_in} ]]; then
  LtExist=true
fi

## create directories
mkdir -p $local_path/
mkdir -p $temp_path

## Get file to temp path
if [[ $LtExist = false ]]; then
  if [[ $LlExist = true ]]; then
    cp $local_path/${file_in} $temp_path/${file_in} 
    echo "file copied from local path"
  else
    wget -q --spider $http_path/${file_in} && LrExist=true || LrExist=false 
    if [[ $LrExist = true ]]; then
      wget -O $temp_path/${file_in}  $http_path/${file_in} 
      echo "file copied from remote server"
    else
      echo "Cannot find file locally or in remote server!"
      exit -9 
    fi
  fi
else
   echo "file already available on local path"
fi 

Lpost=false # indicate if we need to do any post-processing ?
nco_pp=""
if [[ $Plat != -999 ]]; then
  nco_pp="$nco_pp -d lat,$Plat -d lon,$Plon "
  Lpost=true
fi
if [[ $latmin != -999 ]]; then
  nco_pp="$nco_pp  -d lat,$latmin,$latmax -d lon,$lonmin,$lonmax "
  Lpost=true
fi
if [[ $dstart != -999 || $dend != -999 ]]; then
  if [[ $Cfreq != "day" ]]; then
    echo "date selection only available for daily data"
    exit -1
  fi 
  xbase=$(date -d "${Cystart}-01-01" +"%s" )
  xstart0=$(date -d "$dstart" +"%s" )
  xend0=$(date -d "$dend" +"%s" )
  xstart1=$(( ( $xstart0 - $xbase )/86400 ))
  xend1=$(( ( $xend0 - $xbase )/86400 ))
  nco_pp="$nco_pp  -d time,$xstart1,$xend1 "
fi 


if [[ $Lpost = false ]]; then
  cp $temp_path/${file_in} $local_path/${file_in}
else
  if [[ $Creg = NONE ]]; then
    echo "Creg (--rname) must be provided"
    exit -1
  else
    file_out="e2o_${Cid}_${Cver}_${Creg}_${Cfreq}_${Cvar}_${Cystart}-${Cyend}.nc"
    # call nco
    echo "Running command: ncks -O $nco_pp $temp_path/${file_in} $local_path/${file_out} "
    ncks -O $nco_pp $temp_path/${file_in} $local_path/${file_out}
    
  fi
fi 

## clean before leaving 
if [[ $Lclean = true ]]; then
  rm -f $temp_path/${file_in}
fi



exit 0 
