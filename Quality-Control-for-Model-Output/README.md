# Quality Control Checks for Model Output
Test1
This is an initial version of the tool and was only tested with ECMWF data.
Please upload to the ftp server some sample files so that the tool can be further tested.
 
```e2obs_utils.py``` : python module with several utilities to read fields and process file names
```e2obs_check.py``` : python script to perform the check  

###In preparation  
This script to gather the messages information and produce a short report  

Edit the script ```e2obs_check.py``` changing:
```
# it can be computed using "cdo" :  cdo gridarea ecmwf_wrr0_mon_2012.nc garea.nc
fgarea='garea.nc'  

## Location of netcdf files 
floc='./'
## or thredds server folder 
#floc='https://vortices.npm.ac.uk/thredds/dodsC/ECMWFwrr0/'

cID='ecmwf' # instituion id 
cVER='wrr0' # version id 
FOUT='./'   # location for output message files 

## override e2ob default values:
e2obs.SYEAR=1979 # starting year of simulation
e2obs.EYEAR=2012 # last year of simulation
e2obs.NLAT=360
e2obs.NLON=720
```

For the 0.5x0.5 default grid, you can use this file with the grid cell area ```garea.nc``` (included here)

If the script runs correctly, it will produce text files with: error, warning, status and data messages for each year.

The checks are performed to:
1. netCDF dimension sizes and  time information in the netcdf files (e.g: dtmsg_ecmwf_wrr0_1979.txt )
2. Evaluation and closure of grid-point water balance (e.g. wbmsg_ecmwf_wrr0_1979.txt )
  * The water balance in each grid point  
  ```
  Precip+Runoff+Evap = Δ(SWE+SoilMoist,GroundMoist,SurfStor,CanopInt) 
  ```
  * Averaged over one year the two terms of the equation should balance within 5x1.0e-6 kg m-2 s-1(Assuming 1e-6 kg m-2 s-1 is the typical float32 resolution )  
  * Computation of global land means of the different fluxes for consistency check   
3. Evaluation of energy balance (eg. ebmsg_ecmwf_wrr0_1979.txt )  

Each file will contain a log with:
* Wmsg:  - warning messages: should be checked
* Emsg: - error messages: need to be checked 
* Dmsg: - diagnostic messaged (e.g. global means)
* Smsg: - status messages (e.g. opening files, reading variables
