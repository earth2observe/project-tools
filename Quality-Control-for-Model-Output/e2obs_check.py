#!/usr/bin/env python

#  General quality control of e2ob simulations 
#
#  Emanuel Dutra, emanuel.dutra@ecmwf.int
#  v1 November 2014 

## general modules to load 
import glob
import sys
from netCDF4 import Dataset,num2date
import numpy as np
import traceback
import datetime as dt

### specific
import e2obs_utils as e2oU


## specific functions

def date2yrmonday(indate):
  """
  Function to splite date into yr,mon,day

  Parameters:
  ----------
  indate : np.array of type object with datetime
  

  Returns:
  -------
  year,mon,day as np.arrays
  """
  YR = np.array([ xx.year for xx in indate])
  MON = np.array([ xx.month for xx in indate])
  DAY = np.array([ xx.day for xx in indate])
  return YR,MON,DAY

## function to compute a weighted mean of a field "infield" using the weights: grid_area 
def compute_area_mean(infield,grid_area):
  """
  function to compute a weighted mean of a field "infield" using the weights: grid_area 

  Parameters:
  ----------
  infield : np.array with the data
  grid_area: np.array with the grid weights

  Returns:
  -------
  returns: mean of the field
  """
  try:
    tot_area = np.sum(grid_area[~infield.mask])
  except:
    tot_area = np.sum(grid_area)
  xavg = np.sum(infield*grid_area)/tot_area
  return xavg

def check_fname_consistency(finput,validD,msg=None):
  """
  Check file name consistency 

  Parameters:
  ----------
  finput : class(e2oU.fname) : 
  validD : dictionary of valid keys
  msg    : message (optional)

  Returns:
  -------
  msg is changed 
  """

  if msg is None:
    msg = e2oU.init_msg()

  emsg=0
  for att in ['cid','cver','cdomain','cfreq','cvar','ystart','yend']:
    if not getattr(finput,att) in validD[att] :
      msg['Emsg'].append(finput.fname+': attribute:'+att +' with value:'+str(getattr(finput,att))+' is not in the default list' )
      emsg=emsg+1
  if emsg == 0 :
    msg['Smsg'].append(finput.fname+' file name consistency check OK')
  
  
def check_variable_consistency(finput,msg=None):
  """
  Check variables consistency (meta data only 
  
  Parameters:
  ----------
  finput : class(e2oU.fname) : 
  msg    : message (optional)
  
  Returns:
  -------
  message 
  """
  
  if msg is None:
    msg = e2oU.init_msg()
  
  nc = Dataset(finput.fpath,'r')

  ## general check 
  for cvtime in nc.variables.keys():
    if cvtime in ['time','time_counter']: break
  emsg=0
  for cvar in ['lat','lon',cvtime,finput.cvar]:
    for att in ['long_name','units','_FillValue','comment']:
      if att ==  '_FillValue' and cvar != finput.cvar : continue
      if att ==  'comment' and cvar not in ['SurfMoist','RootMoist'] : continue
      if finput.cfreq == "fix" and cvar == "time":  continue
      try:
        getattr(nc.variables[cvar],att)
      except:
        msg['Emsg'].append(finput.fname+': attribute "%s" of variable "%s" not present'%(att,cvar) )
        emsg=emsg+1


  if emsg == 0 :
    msg['Smsg'].append(finput.fname+' variables attributes consistency check OK')
    
  nc.close()

def check_file_coords(finput,msg=None):
  """
  Check file coordinates 
  
  Parameters:
  ----------
  finput : class(e2oU.fname) : 
  msg    : message (optional)
  
  Returns:
  -------
  message 
  """
  if msg is None:
    msg = e2oU.init_msg()
  
  emsg=0
  nc = Dataset(finput.fpath,'r')
  
  vLAT,vLON = e2oU.default_latlon(finput.cdomain)

  if finput.cfreq == "mon":
    nyears=finput.yend-finput.ystart+1
    vTIME = num2date(np.arange(5,365.25*nyears,365.25/12),"days since %4i-01-01 00:00:00"%(finput.ystart))
  elif finput.cfreq == "day":
    dstart=dt.datetime(finput.ystart,1,1).toordinal()
    dend=dt.datetime(finput.yend,12,31).toordinal()
    vTIME = num2date(np.arange(0,dend-dstart+1,1),"days since %4i-01-01 00:00:00"%finput.ystart)
  elif finput.cfreq == "fix":
    pass
  else:
    print "This frequency test is not implemented yet",finput.cfreq
    sys.exit(-1)
  
  for cvtime in nc.variables.keys():
    if cvtime in ['time','time_counter']: break
  if finput.cfreq != "fix":
    vYR,vMON,vDAY = date2yrmonday(vTIME)
    if tcheck:
      fTIME = num2date(nc.variables[cvtime][:],nc.variables[cvtime].units)
    else:
      fTIME=vTIME
      fTIME[0] = num2date(nc.variables[cvtime][0],nc.variables[cvtime].units)
      fTIME[-1] = num2date(nc.variables[cvtime][-1],nc.variables[cvtime].units)
    fYR,fMON,fDAY = date2yrmonday(fTIME)

  fLAT = nc.variables['lat'][:]
  fLON = nc.variables['lon'][:]

  try:
    ddlon = np.abs(np.sum(vLON-fLON))
    ddlat = np.abs(np.sum(vLAT-fLAT))
    if ddlon > np.finfo(np.float32).eps or ddlat > np.finfo(np.float32).eps :
      msg['Emsg'].append(finput.fname+' Lat or Lon arrays in file is not correct')
      emsg=emsg+1
  except:
    msg['Emsg'].append(finput.fname+' Some problem checking lat/lon arrays: check standard output')
    traceback.print_exc()
    emsg=emsg+1

  if finput.cfreq != "fix" :
    try:
      ddyear = np.abs(np.sum(vYR-fYR))
      ddmon = np.abs(np.sum(vMON-fMON))
      ddday = np.abs(np.sum(vDAY-fDAY))
      if ddyear > np.finfo(np.float32).eps or ddmon > np.finfo(np.float32).eps :
        msg['Emsg'].append(finput.fname+' time year/mon arrays in file is not correct')
        emsg=emsg+1
      if ddday > np.finfo(np.float32).eps and finput.cfreq == "day":
        msg['Emsg'].append(finput.fname+' time day arrays in file is not correct')
        emsg=emsg+1
    except:
      msg['Emsg'].append(finput.fname+' Some problem checking time arrays: check standard output')
      traceback.print_exc()
      emsg=emsg+1

  if emsg == 0 :
    msg['Smsg'].append(finput.fname+' file coords check OK')

  nc.close()
  
  
def check_eb(cf,ystart,yend,cdomain,cid,cver,msg=None):
  """
  Energy balance check 

  Parameters:
  ----------
  Returns:
  -------
  """
  rystart=ystart
  ryend=yend
  vLAT,vLON = e2oU.default_latlon(cf.cdomain)
  nlat = len(vLAT)
  nlon = len(vLON)

  grid_area = e2oU.load_grid_area(fgarea)
  cvarsEB=['SWnet','LWnet','Qh','Qle','Qsm','NET']
  if msg is None:
    msg=e2oU.init_msg()


  venB={}
  globM={}  ## global mean values for information only ! 
  for cvar in cvarsEB:
    cf = cf.attr2fpath(cfreq='mon',cvar=cvar,cdomain=cdomain,cid=cid,cver=cver)
    print 'EB, loading:',cvar
    
    if cvar == "NET":
      venB[cvar] = np.zeros((nlat,nlon))
      for cc in cvarsEB[:-1]:
        venB[cvar] = venB[cvar] + venB[cc]
    else:
      xdata,xtime = e2oU.load_nc_var(cf.fpath,cf.cvar,dstart=dt.datetime(rystart,1,1),dend=dt.datetime(ryend,12,31))
      if xdata is None:
        venB[cvar] = np.zeros((nlat,nlon))
        msg['Wmsg'].append("EB: Could not find variable: '%s', setting to zero!'"%(cvar))
      else:
        venB[cvar] = np.mean(xdata,0)
    if cvar == "Qsm":
      venB[cvar] = venB[cvar]*3.34e5*-1.
    globM[cvar] = compute_area_mean(venB[cvar],grid_area)

  for cvar in cvarsEB:
    msg['Dmsg'].append("EB: Global mean of %s %f (W m-2) with %s/%s %f"%
                          (cvar,globM[cvar],cvar,cvarsEB[0],globM[cvar]/globM[cvarsEB[0]]))
  return msg 

def check_wb(cf,ystart,yend,cdomain,cid,cver,msg=None):
  """
  Water balance check 

  Parameters:
  ----------
  Returns:
  -------
  """
  rystart=ystart
  ryend=yend
  dstart=dt.datetime(cf.ystart,1,1).toordinal()
  dend=dt.datetime(cf.yend,12,31).toordinal()
  xTIME = num2date(np.arange(0,dend-dstart+1,1),"days since %4i-01-01 00:00:00"%cf.ystart)
  tinD=[np.nonzero(xTIME==dt.datetime(rystart,1,1))[0][0],np.nonzero(xTIME==dt.datetime(ryend,12,31))[0][0]]
  ndays=tinD[1]-tinD[0]+1
  #print tinD
  #print ndays
  vLAT,vLON = e2oU.default_latlon(cf.cdomain)
  nlat = len(vLAT)
  nlon = len(vLON)

  grid_area = e2oU.load_grid_area(fgarea)
  cvarsWB=['Precip','Runoff','Evap','Stor','NET']
  if msg is None:
    msg=e2oU.init_msg()


  venB={}
  globM={}  ## global mean values for information only ! 
  for cvar in cvarsWB:

    print 'WB, loading:',cvar

    if cvar == "NET":
      venB[cvar] = np.zeros((nlat,nlon))
      for cc in cvarsWB[:-1]:
        venB[cvar] = venB[cvar] + venB[cc]
    elif cvar == "Stor":
      venB[cvar] = np.zeros((nlat,nlon))
      for svar in ['TotMoist','SWE','CanopInt','SurfStor']:
        print 'WB, loading:',svar
        cf = cf.attr2fpath(cfreq='day',cvar=svar,cdomain=cdomain,cid=cid,cver=cver)
        xdata,xtime = e2oU.load_nc_var(cf.fpath,cf.cvar,tinD=tinD)
        if xdata is None:
          xdata = np.zeros((2,nlat,nlon))
          msg['Wmsg'].append("WB: Could not find variable: '%s', setting to zero!'"%(svar))
        venB[cvar] = venB[cvar] + -1*(xdata[1,:,:] - xdata[0,:,:])/(ndays)
    else:
      cf = cf.attr2fpath(cfreq='mon',cvar=cvar,cdomain=cdomain,cid=cid,cver=cver)
      xdata,xtime = e2oU.load_nc_var(cf.fpath,cf.cvar,dstart=dt.datetime(rystart,1,1,0,0,0),dend=dt.datetime(ryend,12,31,23,59,59))
      #if cvar == 'Precip': print xtime
      if xdata is None:
        venB[cvar] = np.zeros((nlat,nlon))
        msg['Wmsg'].append("WB: Could not find variable: '%s', setting to zero!'"%(cvar))
      else:
        venB[cvar] = np.mean(xdata,0)
      venB[cvar] = venB[cvar]*86400. 
    globM[cvar] = compute_area_mean(venB[cvar],grid_area)

  for cvar in cvarsWB:
    msg['Dmsg'].append("WB: Global mean of %s %f (mm day-1) with %s/%s %f"%
                          (cvar,globM[cvar],cvar,cvarsWB[0],globM[cvar]/globM[cvarsWB[0]]))
    if cvar == "NET" : 
      msg['Dmsg'].append('WB:'+" variable %s with gpmin %e, gpmax %e fldmean %e #gp>thr %i"%
                      (cvar,np.min(venB[cvar]),np.max(venB[cvar]),globM[cvar],np.sum(np.abs(venB[cvar])>5e-6*86400.)))
      if np.sum(np.abs(venB[cvar])>5e-6*86400.) > 0:
        msg['Wmsg'].append('WB:'+" variable %s with gpmin %e, gpmax %e fldmean %e #gp>thr %i"%
                      (cvar,np.min(venB[cvar]),np.max(venB[cvar]),globM[cvar],np.sum(np.abs(venB[cvar])>5e-6*86400.)))
    
    # produce map with WB residuals
    # requires plot_utils from pyutils
    #if (cvar == "NET"):
      #from pyutils import plot_utils as pu
      #import matplotlib.pyplot as plt

      #opts={}
      #opts['Clevels']=np.arange(-2,2.5,0.5)*86400*5e-6
      #opts['cmap']=plt.cm.get_cmap('RdBu')
      #fig=pu.plot_map(vLON,vLAT,venB[cvar],titleC='WB residual',titleL=cf.cid,contourf=False,
                      #titleR="%i #gp"%np.sum(np.abs(venB[cvar])>5e-6*86400.),Clabel='[mm/day]',**opts)
      #fig[0].savefig('map_wb_res_%s_%s_%s_%i_%i.png'%(cf.cid,cf.cver,cf.cdomain,cf.ystart,cf.yend),bbox_inches="tight",dpi=200)
      #plt.close(fig[0])
      
  return msg 

def read_args():
  """
  Get arguments frmo command line 

  Parameters:
  ----------
  Returns:
  -------
  """
  import argparse
  parser = argparse.ArgumentParser(description='Earth2Observe quality control check')
  parser.add_argument('-b',dest='fbase',default='./',type=str,metavar='fbase',
                      help='path to folder containing netcdf files ')
  parser.add_argument('-g',dest='fgarea',default='./garea.nc',type=str,metavar='fgarea',
                      help='path to file containing grid area')
  parser.add_argument('-ys',dest='ystart',default=1979,type=int,metavar='ystart',
                      help='Start year of simulations')
  parser.add_argument('-ye',dest='yend',default=2012,type=int,metavar='yend',
                      help='End year of simulations')
  parser.add_argument('-d',dest='cdomain',default="glob30",type=str,metavar='cdomain',
                      help='simulations domain')
  parser.add_argument('-i',dest='cid',default="ecmwf",type=str,metavar='cid',
                      help='institution id')
  parser.add_argument('-v',dest='cver',default="wrr1",type=str,metavar='cver',
                      help='simulations version')
  parser.add_argument('-t',dest='tcheck',default=False,action='store_true',
                      help='if present check all timesteps (slow), otherwise only 1st and last step')
  args =  parser.parse_args()
  return args 

##==============================================
##==============================================
## MAIN SCRIPT
 #python e2obs_check.py -b ./ -g ./garea.nc -ys 1979 -ye 2012 -d glob30 -i ecmwf -v wrr1

##================================================
##0 . get command line arguments 
args=read_args()
fbase=args.fbase          #'/scratch/rd/need/tmp/e2obs/g76h/'  # folder location of the netcdf files 
fgarea=args.fgarea        #'/scratch/rd/need/tmp/e2obs/g57n/garea.nc'  # location of the garea.nc file 

## defaults
ystart=args.ystart       #1979 start year
yend=args.yend          #2012  end year
cdomain=args.cdomain       #"glob30"  simulations domain
cid=args.cid           #"ecmwf"  institution id 
cver=args.cver          #"wrr1"    simulations version id 
tcheck=args.tcheck

print args
#sys.exit()
##=======================================================
## 1. File consistency checks: we loop on all possible variables:
msg=e2oU.init_msg() # intialize message dictionary 
cf = e2oU.fname()   # initialize file name class 

# loop on all possible variables / frequencies
for cvar in e2oU.validD['cvar']:
  for cfreq in ['day','mon','fix']:
    if cfreq == 'fix' and cvar not in e2oU.validD['cvar_fix']:
      continue
    if cvar in e2oU.validD['cvar_fix'] and cfreq != 'fix':
      continue
    cf=cf.attr2fpath(base=fbase,cfreq=cfreq,cvar=cvar,cdomain=cdomain,
                     ystart=ystart,yend=yend,cid=cid,cver=cver)
    print "checking:", cf.fpath


    # 1.1 :check if file can be opened ! 
    try:
      nc = Dataset(cf.fpath,'r')
    except:
      msg['Wmsg'].append(cf.fname+': cannot open netcdf file' )
      continue
    nc.close()
    
    ## 1.2 : check that file name is consistent (should be !)
    check_fname_consistency(cf,e2oU.validD,msg)

    # 1.3 : Check if the variable attributes are ok
    check_variable_consistency(cf,msg)
    
    # 1.4 : check the coordinate attributes 
    check_file_coords(cf,msg)

##===========================================
## 2. Energy check 
cf = e2oU.fname()
try:
  cf=cf.attr2fpath(base=fbase,cfreq='mon',cvar='SWnet',cdomain=cdomain,
                     ystart=ystart,yend=yend,cid=cid,cver=cver)
  msg = check_eb(cf,ystart,yend,cdomain,cid,cver,msg)
except:
  msg['Wmsg'].append('cannot find SWnet file: energy balance cannot be checked' )


##===========================================
## 3. Water balance
cf = e2oU.fname()
#try:
cf=cf.attr2fpath(base=fbase,cfreq='mon',cvar='Precip',cdomain=cdomain,
                   ystart=ystart,yend=yend,cid=cid,cver=cver)
msg = check_wb(cf,ystart,yend,cdomain,cid,cver,msg)
#except:
  #msg['Wmsg'].append('cannot find Precip file: Water balance cannot be checked' )

#===========================================
#4. save message to output:
print 'saving output to: ','check_%s_%s_%s.txt'%(cid,cver,cdomain)
e2oU.write_msg2txt(msg,'check_%s_%s_%s.txt'%(cid,cver,cdomain))
