#!/bin/ksh 
# Kornshell Script 
# Check if files are available and create an html page with the result
# Provider ECMWF 

set -u

ver=$1 #"wrr1" 
freq0=$2 #"mon"


ids="ecmwf univu metfr nerc jrc cnrs univk csiro eth"
cvars="Precip Evap Runoff SWE SurfMoist RootMoist TotMoist Rainf Qs Qsb Qrec Qsm PotEvap ECanop TVeg ESoil EWater "
cvars+="RivOut Dis SWnet LWnet Qle Qh AvgSurfT Albedo LAI  CanopInt SWEVeg SurfStor "
cvars+="WaterTableD SnowFrac SnowDepth  GroundMoist "
cvars+="lsm SurfSoilSat RootSoilSat TotSoilSat"

# cvars="Evap"
 
if [[ $ver = "wrr1" ]];then
  ystart=1979
  yend=2012
  domain=glob30
  ids="ecmwf univu metfr nerc jrc cnrs univk csiro eth"
elif [[ $ver = "wrr2" ]];then
  ystart=1980
  yend=1989
  domain=glob15
  ids="ecmwf univu metfr nerc jrc cnrs univk anu"
fi
fout=e2o_resume_${ver}_${freq0}_${ystart}${yend}_$(date +"%Y-%m-%d").html # output html file 

echo "<html>
<head> 
<title>tmp </title>
</head>
<body>
<table border=\"1\"> " > $fout

echo "<tr><td>cvar</td>" >> $fout
for cid in $ids
do
  echo "<td>$cid</td>" >> $fout
done
echo "</tr>" >> $fout

for cvar in $cvars
do
  echo "<tr><td>$cvar</td>" >> $fout
  for cid in $ids
  do
    freq=$freq0
    case $cvar in
     lsm|SurfSoilSat|RootSoilSat|TotSoilSat) freq="fix";;
    esac
     Lexist=true
    ./extract_E2OBS_simulations.ksh -e $ver --id $cid --variable $cvar --frequency $freq --ystart $ystart --yend $yend -d $domain -c 1>out_extract 2>&1 || Lexist=false
    echo $cid $cvar $Lexist
    if [[ $Lexist = true ]]; then
      url=$( cat out_extract | grep "fileurl" | awk '{print $2}' )
      dap=$( cat out_extract | grep "opendap" | awk '{print $2}' )
      echo "<td><a href=\"$url\">url</a>,<a href=\"$dap\">dap</a></td>" >> $fout
    else
      echo "<td><b>NA</b></td>" >> $fout
#       cat out_extract
    fi
    rm -f out_extract
  done
  echo "</tr>" >> $fout
done

echo "</table>
</body>
</html>" >> $fout
