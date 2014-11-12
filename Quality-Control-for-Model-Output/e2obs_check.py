#!/usr/bin/env python

#  General quality control of e2ob simulations 
#
#  Emanuel Dutra, emanuel.dutra@ecmwf.int
#  v0 August 2014 

## general modules to load 
import sys
from netCDF4 import Dataset,date2num,date2index,num2date
import time
import datetime
import os
import ntpath
import numpy as np
import pandas as pd 

## specific 
import e2obs_utils as e2obs


##==============================================

## function to compute a weighted mean of a field "infield" using the weights: grid_area 
def compute_area_mean(infield,grid_area):
  try:
    tot_area = np.sum(grid_area[~infield.mask])
  except:
    tot_area = np.sum(grid_area)
  xavg = np.sum(infield*grid_area)/tot_area
  return xavg

##  Function to check file dimensions 
def check_dims(fname,msg=None):

  if msg is None:
    msg = e2obs.init_msg()
  ctag=ntpath.basename(fname)+' dims:'
  #print "Checking dimensions of:%s"%(fname)
  finfo = e2obs.get_info_from_file(fname)
  vdims = e2obs.dim_size(finfo)
  try: 
    nc = Dataset(fname,'r')
  except:
    print "could not load file"
    print fname 
    print "cannot continue check !!!"
    sys.exit(-1)

  #dimension sizes 
  for vdim in ['time','lat','lon','nlevs']:
    if vdim in nc.dimensions.keys():
      if (len(nc.dimensions[vdim]) != vdims[vdim]) and (vdims[vdim] > 0 ):
        msg['Emsg'].append(ctag+'Dimension %s has %i while it should have %i elements'%(vdim,len(nc.dimensions[vdim]),vdims[vdim]))
      else:
        msg['Smsg'].append(ctag+'Found dimension %s with correct %i elements'%(vdim,len(nc.dimensions[vdim])))
    else:
      msg['Emsg'].append(ctag+'Dimension %s was not found '%(vdim))
  nc.close()
  return msg 


##=============================================
## function to check time dimensions 

def check_time(fname,msg=None):

  if msg is None:
    msg = e2obs.init_msg()
  ctag=ntpath.basename(fname)+' time:'

  finfo = e2obs.get_info_from_file(fname)
  iYEAR=int(finfo['cYEAR'])
  vdims = e2obs.dim_size(finfo)
  nc = Dataset(fname,'r')

  # check time 
  try:
    mtime =  pd.to_datetime(num2date(nc.variables['time'][:],nc.variables['time'].units))
    if finfo['cFREQ'] == 'day':
      vtime = pd.date_range(pd.datetime(iYEAR,1,1,0,0), periods=vdims['time'],freq='D')
    if finfo['cFREQ'] == 'mon':
      vtime = pd.date_range(pd.datetime(iYEAR,1,1,0,0), periods=vdims['time'],freq='MS')
    tdiff  = ((mtime.asi8-vtime.asi8)/1e9/3600)  # difference in hours 
    if np.sum(tdiff != 0 ) > 0:
      msg['Wmsg'].append(ctag+'Found %i different time values from %s with max %f min %f mean %f hours differences'%
                  (np.sum(tdiff != 0 ),str(vtime[0]),np.max(tdiff),np.min(tdiff),np.mean(tdiff)))
    else:
      msg['Smsg'].append(ctag+'time variable check: OK')
  except:
    msg['Emsg'].append(ctag+'Could not check time information, check time variable and units attributes')
  
  return msg 


##=================================================
## function to check water balance 
def eval_wb(fnames,fgarea,msg=None):

  if msg is None:
    msg = e2obs.init_msg()
  dfinfo = e2obs.get_info_from_file(fnames['day'])

  grid_area = e2obs.load_grid_area(fgarea)


  ## water balance components
  cevapC=['ECanop','TVeg','ESoil','EWater']  # evaporation components 
  crunoffC=['Qs','Qsb','Qrec']               #  runoff components  
  cwatbC=['Precip','Runoff','Evap','Rainf','Qsm'] # water balance components 

  ctag='WB %s '%dfinfo['cYEAR']
  globM={}  ## global mean values for information only ! 

  # 1. load water balance components:
  vwatbC={}
  for cvar in cwatbC:
    xdata,xxtimeWB,msg = e2obs.load_nc_var(fnames['mon'],cvar,msg=msg)
    vwatbC[cvar] = np.mean(xdata,0) # temporal mean 
    globM[cvar] = compute_area_mean(vwatbC[cvar],grid_area)
    
  ## compute TWSV from water storage reservoirs:
  vdims = e2obs.dim_size(dfinfo)
  tinD=[0,vdims['time']-1] # first and last day for the daily file 
  ndays=tinD[1]-tinD[0]+1  # number of days 
  vwatS={}
  cwatS=['SWE','SoilMoist','CanopInt','TWSV','flxC','TWSV_stor']
  for cvar in cwatS:
    if cvar == 'TWSV': # TWSV from the fluxes 
      vwatS[cvar]  = vwatbC['Precip']+vwatbC['Runoff']+vwatbC['Evap']
    elif cvar == 'TWSV_stor':  # TWSV from the state variables 
      vwatS[cvar] =  vwatS['SWE']+vwatS['SoilMoist']+vwatS['CanopInt']+vwatS['flxC']
    elif cvar == 'flxC':  # daily fluxes correction since the state variables are daily means 
      vwatS[cvar] = vwatS['SWE']*0.
      for cvar1 in ['Rainf','Evap','Runoff']:
        xdata,xxtime,msg = e2obs.load_nc_var(fnames['day'],cvar1,tinD=tinD,msg=msg)
        vwatS[cvar] = vwatS[cvar]+0.5*(xdata[1,:,:]+xdata[0,:,:])/(ndays)
    else:
      xdata,xxtimeS,msg = e2obs.load_nc_var(fnames['day'],cvar,tinD=tinD,msg=msg)
      if cvar == 'SoilMoist': # total soil moisture 
        xdata = np.sum(xdata,1).squeeze()
      vwatS[cvar] = (xdata[1,:,:]-xdata[0,:,:])/(ndays*86400)
    globM[cvar] = compute_area_mean(vwatS[cvar],grid_area)

  ## water balance mismatch 
  vwatS['TWSV_res'] = vwatS['TWSV']-vwatS['TWSV_stor']
  globM['TWSV_res'] = compute_area_mean(vwatS['TWSV_res'],grid_area)
  for cvar in ['TWSV','TWSV_stor','TWSV_res']:
    xx = vwatS[cvar]
    xx[grid_area == 0] =0.
    msg['Dmsg'].append(ctag+"variable %s with gpmin %e, gpmax %e fldmean %e #gp>thr %i"%
                      (cvar,np.min(xx),np.max(xx),compute_area_mean(np.abs(xx),grid_area),np.sum(np.abs(xx)>5e-6)))
    if cvar == 'TWSV_res':
      if np.sum(np.abs(xx)>5e-6) > 0 :
        msg['Wmsg'].append(ctag+"There are grid points with TWSV residual above 5e-6 kg m-2 -s-1 - check WB closure carefully")

  for cvar in cwatbC+['TWSV','TWSV_stor','TWSV_res']:
    msg['Dmsg'].append(ctag+"Global mean of %s %f (mm/day) with %s/Precip %f"%
                      (cvar,globM[cvar]*86400.,cvar,globM[cvar]/globM['Precip']))

  # 2. check/load evap. components
  vevapC={}
  tevapC = vwatbC['Evap']*0.
  for cvar in cevapC:
    xdata,xxtime,msg = e2obs.load_nc_var(fnames['mon'],cvar,msg=msg)
    vevapC[cvar] = np.mean(xdata,0)
    globM[cvar] = compute_area_mean(vevapC[cvar],grid_area)
    tevapC = tevapC + vevapC[cvar]

  # the residual is set as SubSnow (maybe not the best approach?)
  vevapC['SubSnow'] = vwatbC['Evap'] - tevapC
  globM['SubSnow'] = compute_area_mean(vevapC['SubSnow'],grid_area)

  #print 
  for cvar in ['Evap']+cevapC+['SubSnow']:
    msg['Dmsg'].append(ctag+"Global mean of %s %f (mm/day) with %s/Evap %f"%
                      (cvar,globM[cvar]*86400.,cvar,globM[cvar]/globM['Evap']))
  
  # 3. check/load runoff
  vrunoffC={}
  for cvar in crunoffC:
    xdata,xxtime,msg = e2obs.load_nc_var(fnames['mon'],cvar,msg=msg)
    vrunoffC[cvar] = np.mean(xdata,0)
    globM[cvar] = compute_area_mean(vrunoffC[cvar],grid_area)

  for cvar in ['Runoff']+crunoffC:
    msg['Dmsg'].append(ctag+"Global mean of %s %f (mm/day) with %s/Runoff %f"%
                      (cvar,globM[cvar]*86400.,cvar,globM[cvar]/globM['Runoff']))
  return msg


##===========================================================
## Energy balance check 
def eval_eb(fnames,fgarea,msg=None):
  if msg is None:
    msg = e2obs.init_msg()
  dfinfo = e2obs.get_info_from_file(fnames['day'])
  grid_area = e2obs.load_grid_area(fgarea)

  ## energy balance components
  cenbC=['LWnet','SWnet','Qh','Qle','SFCnet']
  ctag='EB %s '%dfinfo['cYEAR']
  globM={}  ## global mean values for information only ! 

  ## load variables
  venbC={}
  for cvar in cenbC:
    if cvar == 'SFCnet':
      venbC[cvar] = venbC['LWnet']+venbC['SWnet']+venbC['Qh']+venbC['Qle']
    else:
      xdata,xxtimeEB,msg = e2obs.load_nc_var(fnames['mon'],cvar,msg=msg)
      venbC[cvar] = np.mean(xdata,0) # temporal mean 
    globM[cvar] = compute_area_mean(venbC[cvar],grid_area)

  for cvar in cenbC:
      msg['Dmsg'].append(ctag+"Global mean of %s %f (W m-2) with %s/SWnet %f"%
                        (cvar,globM[cvar],cvar,globM[cvar]/globM['SWnet']))
  return msg 


##=========================================================
## Main script here 

# location of grid cell area
# it can be computed using "cdo" :  cdo gridarea ecmwf_wrr0_mon_2012.nc garea.nc
fgarea='./garea.nc'  

## Location of netcdf files 
#floc='/scratch/rd/need/tmp/e2obs/g57n/'
## or thredds server folder 
floc='https://vortices.npm.ac.uk/thredds/dodsC/ECMWFwrr0/'

cID='ecmwf' # instituion id 
cVER='wrr0' # version id 
FOUT='./'   # location for output message files 

## override e2ob default values:
e2obs.SYEAR=1979 # starting year of simulation
e2obs.EYEAR=2012 # last year of simulation
e2obs.NLAT=360
e2obs.NLON=720


## loop on years 
for year in range(e2obs.SYEAR,e2obs.EYEAR+1):

  # initialize the messages dictionaries 
  dtmsg = e2obs.init_msg()
  wbmsg = e2obs.init_msg()
  ebmsg = e2obs.init_msg()
  
  cYEAR=str(year)
  fnames={}
  fnames['day'] = e2obs.gen_file_name(floc,cYEAR,cID,cVER,'day')
  fnames['mon'] = e2obs.gen_file_name(floc,cYEAR,cID,cVER,'mon')
  print "Processing:"
  print fnames
  
  ## check dim/time of files
  print "Checking dim/time "
  for fname in fnames.keys():
    dtmsg = check_dims(fnames[fname],msg=dtmsg)
    dtmsg = check_time(fnames[fname],msg=dtmsg)

  print "Checking wb"
  wbmsg = eval_wb(fnames,fgarea,msg=wbmsg)

  print "Checking eb"
  ebmsg = eval_eb(fnames,fgarea,msg=ebmsg)
  
  ## write messages to text files 
  e2obs.write_msg2txt(dtmsg,'reports/'+FOUT+'dtmsg_%s_%s_%s.txt'%(cID,cVER,cYEAR))
  e2obs.write_msg2txt(wbmsg,'reports/'+FOUT+'wbmsg_%s_%s_%s.txt'%(cID,cVER,cYEAR))
  e2obs.write_msg2txt(ebmsg,'reports/'+FOUT+'ebmsg_%s_%s_%s.txt'%(cID,cVER,cYEAR))




