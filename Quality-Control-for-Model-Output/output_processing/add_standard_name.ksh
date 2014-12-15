#!/bin/ksh 
# script to append the attribute "standard_name" to the netcdf variables 
#  change the FLOC to the full path of the folder containing the files 
#  If the variable does not have a CF standard_name the attribute is set == variable name 

set -eu 
FLOC="./"  # location of files 

cd $FLOC
for ff in $(ls e2o_*.nc)
do
  cvar=$(echo $ff | sed  's/_/ /g' | sed 's/\./ /g' | awk '{print $6}')
  case $cvar in
  Precip) sname="precipitation_flux";;
  Evap) sname="water_evaporation_flux";;
  Runoff) sname="runoff_flux";;
  Rainf) sname="rainfall_flux";;
  Qs) sname="surface_runoff_flux";;
  Qsb) sname="subsurface_runoff_flux";;
  Qsm) sname="surface_snow_melt_flux";;
  PotEvap) sname="water_potential_evaporation_flux";;
  ECanop) sname="water_evaporation_flux_from_canopy";;
  TVeg) sname="transpiration_flux" ;;
  ESoil) sname="water_evaporation_flux_from_soil" ;;
  SWnet) sname="surface_net_downward_shortwave_flux";;
  LWnet) sname="surface_net_downward_longwave_flux";;
  Qle) sname="surface_downward_latent_heat_flux";;
  Qh) sname="surface_downward_sensible_heat_flux";;
  AvgSurfT) sname="surface_temperature";;
  Albedo) sname="surface_albedo";;
  LAI) sname="leaf_area_index";;
  SWE) sname="liquid_water_content_of_surface_snow";;
  SnowFrac) sname="surface_snow_area_fraction";;
  SnowDepth) sname="surface_snow_thickness";;
  lsm) sname="land_area_fraction";;
   *) echo "no standard name found "; sname=$cvar ;;
  esac
  echo "Processing variable: $cvar with $sname in file: $ff"
  ncatted -O -a "standard_name",$cvar,a,c,"$sname" $ff 
done 
