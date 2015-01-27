#!/bin/ksh
# Kornshell Script to extract E2OBS Meteorological forcing 
# "met_forcing_v0" : 1979-2012 tri-hourly (daily) global land, lakes, ocean
# Download from the Threads server: http://wci.earth2observe.eu/thredds
# Provider ECMWF 
# Script setup---------------------------------------------
forcing_version=met_forcing_v0
#data_label=daily_E2OBS           #obtain daily-mean fields
data_label=E2OBS                  #obtain tri-hourly fields
#startyear=1979
startyear=2012
endyear=2012
# ---------------------------------------------------------

year=$startyear
while [ $year -le $endyear ] ; do
for VAR in SWdown LWdown Rainf Snowf PSurf Tair Qair Wind ; do
  month=1
  while [ $month -le 12 ] ; do
   yyyymm=`expr ${year} \* 100 + ${month}` 
#  echo wget http://wci.earth2observe.eu/thredds/fileServer/ecmwf/met_forcing_v0/${year}/${VAR}_E2OBS_${yyyymm}.nc
   wget http://wci.earth2observe.eu/thredds/fileServer/ecmwf/met_forcing_v0/${year}/${VAR}_${data_label}_${yyyymm}.nc
   month=`expr $month + 1`
  done
 done
 year=`expr $year + 1`
done
