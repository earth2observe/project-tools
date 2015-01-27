#!/bin/ksh 
# Kornshell Script 
# Check if files are available and create an html page with the result
# Provider ECMWF 

set -u

ids="ecmwf univu metfr nerc jrc cnrs univk csiro eth"
cvars="Precip Evap Runoff Rainf Qs Qsb Qrec Qsm PotEvap ECanop TVeg ESoil EWater "
cvars+="RivOut Dis SWnet LWnet Qle Qh AvgSurfT Albedo LAI SWE CanopInt SWEVeg SurfStor "
cvars+="WaterTableD SnowFrac SnowDepth SurfMoist RootMoist TotMoist GroundMoist "
cvars+="lsm SurfSoilSat RootSoilSat TotSoilSat"


fout=e2o_resume_$(date +"%Y-%m-%d").html # output html file 

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
    freq="day"
    case $cvar in
     lsm|SurfSoilSat|RootSoilSat|TotSoilSat) freq="fix";;
    esac
     Lexist=true
    ./extract_E2OBS_simulations.ksh --id $cid --variable $cvar --frequency $freq -c 1>out_extract 2>&1 || Lexist=false
    echo $cid $cvar $Lexist
    if [[ $Lexist = true ]]; then
      url=$( cat out_extract | awk '{print $2}' )
      echo "<td><a href=\"$url\">$freq</a></td>" >> $fout
    else
      echo "<td><b>NA</b></td>" >> $fout
    fi
    rm -f out_extract
  done
  echo "</tr>" >> $fout
done

echo "</table>
</body>
</html>" >> $fout