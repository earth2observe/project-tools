# Examples for data access 

**download_E2OBS_Met_forcing_wget.ksh**

Example script to download the meteorological forcing 

**check_files.ksh**

Example script to list all the available data in server as a html page 

**extract_E2OBS_simulations.ksh**

Script to extract / sample E2OB simulation 

**Examples**


For description of command line options: 
```
./extract_E2OBS_simulations.ksh --man 
```

Check if a file exists in the dataserver
```
./extract_E2OBS_simulations.ksh --id=ecmwf --variable=SWE --frequency=day  -c
returns 0 if file exists, or -9 if file is not present 
see "check_files.ksh with an example 
```

Extract the montlhy evaporation from all models
```
cids="ecmwf univu metfr nerc jrc cnrs univk csiro eth" # list of all institutions
datadir="./"  # base location to save files 
for cid in $cids
do
  ./extract_E2OBS_simulations.ksh --datadir=$datadir \
                      --id=$cid \
                      --variable=Evap \
                      --frequency=mon 
done 
```

Extract the daily evaporation for a list of lat/lon points for ecmwf simulation
```
set -A rname  reading  paris  lasvegas
set -A plat   51.5     49.0     36.0 
set -A plon   0.5      2.1    -245.0
ikp=0
np=$(( ${#rname[*]} - 1 ))
while [[ $ikp -le $np ]]
do
  doclean="-y" # do not remove file to avoid downloading every time 
  if [[ $ikp = $np ]]; then 
    doclean=""
  fi
  ./extract_E2OBS_simulations.ksh --datadir=$datadir $doclean \
                      --id=ecmwf \
                      --variable=Evap \
                      --frequency=day \
                      --plat=${plat[ikp]} \
                      --plon=${plon[ikp]} \
                      --rname=${rname[ikp]} 
  ikp=$(( $ikp + 1 ))
done
```

Extract the monthly evaporation for a region 
```
./extract_E2OBS_simulations.ksh --datadir=$datadir \
                    --id=ecmwf \
                    --variable=Evap \
                    --frequency=mon \
                    --latmin=35. \
                    --latmax=60. \
                    --lonmin=-11. \
                    --lonmax=35. \
                    --rname=europe
```                  

Extract the daily evaporation for a region for the period 2001-01-03 to 2003-03-15
```
./extract_E2OBS_simulations.ksh --datadir=$datadir -y -w \
                    --id=ecmwf \
                    --variable=Evap \
                    --frequency=day \
                    --latmin=35. \
                    --latmax=60. \
                    --lonmin=-11. \
                    --lonmax=35. \
                    --dstart=20010103 \
                    --dend=20030315 \
                    --rname=europe-myperiod
```


