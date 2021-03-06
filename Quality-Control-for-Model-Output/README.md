# Quality Control Checks for Model Output

New version including the updated file naming structure

```e2obs_utils.py``` : python module with several utilities to read fields and process file names
```e2obs_check.py``` : python script to perform the check  

**Usage**
```
python e2obs_check.py -h
usage: e2obs_check.py [-h] [-b fbase] [-g fgarea] [-ys ystart] [-ye yend]
                      [-d cdomain] [-i cid] [-v cver]

Earth2Observe quality control check

optional arguments:
  -h, --help  show this help message and exit
  -b fbase    path to folder containing netcdf files
  -g fgarea   path to file containing grid area
  -ys ystart  Start year of simulations
  -ye yend    End year of simulations
  -d cdomain  simulations domain
  -i cid      institution id
  -v cver     simulations version
```
**Example**

Assuming all the model files are in the folder "/somelocation/
```
Local files:
python e2obs_check.py -b "/someloaction/" -g ./garea.nc -ys 1979 -ye 2012 -d glob30 -i ecmwf -v wrr1
Remote files on the thredds server
python e2obs_check.py -b https://wci.earth2observe.eu/thredds/dodsC/ecmwf/wrr1/ -g ./garea.nc -ys 1979 -ye 2012 -d glob30 -i ecmwf -v wrr1
```

If the script runs correctly, it will produce text file with: error, warning, status and data messages.
The example output ```check_ecmwf_wrr1_glob30.txt```

The checks are performed to:

1. File consistency checks:
  * Loop on all possible variable names and temporal frequencies
    * If a file is not found it is reported as a warning
  * File name consistency: ```check_fname_consistency```
  * Variable attributes: ```check_variable_consistency```
  * File coordinates: ```check_file_coords```
2. Evaluation of energy balance: ```check_eb```
  * Computes the net energy as:
  ```
  SWnet+LWnet+Qle+Qh = residual
  ```
3. Evaluation and closure of grid-point water balance: ```check_eb```
  * The water balance in each grid point  
  ```
  Precip+Runoff+Evap = Δ(SWE+SoilMoist,GroundMoist,SurfStor,CanopInt) 
  ```
  * Averaged over the full period the two terms of the equation should balance within 5x1.0e-6 kg m-2 s-1 
  * Computation of global land means of the different fluxes for consistency check

Each file will contain a log with:
* Wmsg:  - warning messages: should be checked
* Emsg: - error messages: need to be checked 
* Dmsg: - diagnostic messaged (e.g. global means)
* Smsg: - status messages (e.g. opening files, reading variables
