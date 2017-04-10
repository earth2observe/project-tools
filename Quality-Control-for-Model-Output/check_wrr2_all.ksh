#!/bin/ksh 

# batch script to check all WRR2 files on the thedds server 

## ecmwf
for cid in ecmwf metfr ceh univk jrc 
do 
  # wrr2
#   ./e2obs_check.py -b http://wci.earth2observe.eu/thredds/dodsC/$cid/wrr2/ -v wrr2  -ys 1980 -ye 2014 -d glob15 -i $cid -s
  # wrr2*
  for ver in wrr2cmorph wrr2da wrr2gsmap wrr2trmm wrr2trmmrt
  do
    ./e2obs_check.py -b http://wci.earth2observe.eu/thredds/dodsC/$cid/$ver/ -v $ver  -ys 2000 -ye 2013 -d glob15 -i $cid
  done
done 
# special case for anu
cid=anu
ver=wrr2da
./e2obs_check.py -b http://wci.earth2observe.eu/thredds/dodsC/$cid/wrr2/ -v $ver  -ys 2000 -ye 2014 -d glob15 -i $cid 
