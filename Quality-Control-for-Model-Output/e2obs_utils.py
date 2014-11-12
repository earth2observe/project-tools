#!/usr/bin/env python

#  General quality control of e2ob simulations 
#
#  Emanuel Dutra, emanuel.dutra@ecmwf.int
#  v0 August 2014 

## general modules to load 
import sys
import ntpath
import re
from netCDF4 import Dataset,date2num,date2index,num2date
import time
import datetime
import numpy as np


## Default values, can be changed by calling scripts
SYEAR=1979 # starting year of simulation
EYEAR=2012 # last year of simulation
NLAT=360
NLON=720

## General definitions : (this should not be changed !)
Valid_cID=['ecmwf','univu','metfr','nerc','jrc','cnrs','univk','ambio','csiro'] # valid list of model iDs
Valid_cVER=['wrr0','wrr1','wrr2'] # valid list of experiment name
Valid_cFREQ=['day']               # valid list of output frquencies



def load_grid_area(fgarea,cvar='cell_area'):
  """
  Load "cell_area" for global mean computations
  
  Parameters:
  ----------
  fgarea : str : path for netcdf file containing the cell areas 
  cvar   : str : netcdf variable name, default == 'cell_area'
  
  Returns:
  -------
  grid_area : np.array with the grid cell area (the units are not important!)
  """
  nc = Dataset(fgarea,'r')
  grid_area = nc.variables['cell_area'][:]
  nc.close()
  return grid_area

def dim_size(finfo):
  """
  Find the expected netcdf dimensions
  
  Parameters:
  ----------
  finfo  : dictionary containing the file information 
  
  Returns:
  -------
  vdims : dictionary containing the expected netcdf dimensions: 
          nlevs = -1 (any number of soil level)
          lat   = # latitudes
          lon   = # longitudes
          time  = # time stamps (depends if it is a monthly or a daily file 
  """

  iYEAR=int(finfo['cYEAR'])

  # valid dimension sizes 
  vdims={}
  vdims['nlevs']=-1
  vdims['lat']=NLAT
  vdims['lon']=NLON
  if finfo['cFREQ'] == 'mon':
    vdims['time']=12
  if finfo['cFREQ'] == 'day':
    vdims['time']=365 + 1*(np.mod(iYEAR,4)==0)
  return vdims

def print_msg(msg):
  """
  Prints to screen the messages 
  
  Parameters:
  ----------
  msg  : dictionary containing messages 
  """
  for msgT in msg.keys():
    print "======================"
    print msgT,':',len(msg[msgT])
    for imsg in msg[msgT]:
      print imsg

def write_msg2txt(msg,fout):
  """
  Write to a file the messages
  
  Parameters:
  ----------
  msg  : dictionary containing messages 
  fout : path of file name to write the messages
  """
  f = open(fout,'w')
  for msgT in msg.keys():
    f.write("======================\n")
    f.write(msgT+':'+str(len(msg[msgT]))+"\n")
    for imsg in msg[msgT]:
      f.write(imsg+"\n")
  f.close()

def init_msg():
  """
  Initialize a message dictionary 
  
  Parameters:
  ----------
  none
  
  Returns:
  -------
  msg : dictionary for the different messages: 
        Smsg: Status related messages (verbose output of what was done / found) 
        Dmsg: Data related messages - contain global means of the variables 
        Wmsg: Warning messages : this should be carefully checked 
        Emsg: Error messages:  Errors found in the dataset : these should be addressed before the final release. 
  """
  msg={}
  msg['Smsg']=[]
  msg['Wmsg']=[]
  msg['Emsg']=[]
  msg['Dmsg']=[]
  return msg 

def gen_file_name(floc,cYEAR,cID,cVER,cFREQ,stop_warning=True):
  """
  Generate file name 
  
  Parameters:
  ----------
  floc : str, main folder location with the files 
  cYEAR: str, character year in the form yyyy
  cID  : str, institution iD 
  cVER : str, tag denoting the experiment name 
  cFREQ : str, frequency tag 
  stop_warning: logical(optional), if True exist if some error is found default is True

  Returns:
  -------
  cfile : str, full path for file
  """

  cfile = None # default return: if file does not exist or some error in the input
  ## generic checks: 
  iyear = int(cYEAR)
  if iyear < SYEAR or iyear > EYEAR:
    print "WARNING: eobs_utils -> gen_file_name"
    print "input year must be between %i and %i and was provided: %i"%(SYEAR,EYEAR,iyear)
  elif cID not in Valid_cID:
    print "WARNING: eobs_utils -> gen_file_name"
    print "input institution id (cID) is not valid: %s "%(cID)
    print "valid values are:",Valid_cID
  elif cVER not in Valid_cVER:
    print "WARNING: eobs_utils -> gen_file_name"
    print "input version (cVER) is not valid: %s "%(cVER)
    print "valid values are:",Valid_cVER
  elif cFREQ not in Valid_cFREQ:
    print "WARNING: eobs_utils -> gen_file_name"
    print "input output frequency (cFREQ) is not valid: %s "%(cFREQ)
    print "valid values are:",Valid_cFREQ 
  else:
    # maybe we can get a file name ?
    cfile1 = "%s/%s_%s_%s_%s.nc"%(floc,cID,cVER,cFREQ,cYEAR)
    #if not ntpath.isfile(cfile1):
      #print "WARNING: eobs_utils -> gen_file_name"
      #print "Generated file name is not a file ?: %s "%(cfile1)
    #else:
    cfile = cfile1 

  if cfile is None:
    print "WARNING: eobs_utils -> gen_file_name"
    print "Some error occured, generated file name is None"
    if stop_warning:
      sys.exit(-1)
  return cfile
  
def get_info_from_file(cfile):
  """
  Get information from file name 
  
  Parameters:
  ----------
  cfile : str, full path for file (or at least file name)
  
  Returns:
  -------
  finfo : dictionary with the following keys:
    floc : str, main folder location with the files 
    cYEAR: str, character year in the form yyyy
    cID  : str, institution iD 
    cVER : str, tag denoting the experiment name 
    cFREQ : str, frequency tag 
  """
  finfo = {}
  finfo['floc'] = ntpath.dirname(cfile)
  bname=re.split('_|\.',ntpath.basename(cfile))
  if len(bname) != 5:
    print "Error: eobs_utils -> get_file_name"
    print "File name does not seem correct!",ntpath.basename(cfile)
    sys.exit(-1)
  finfo['cID'] = bname[0]
  finfo['cVER'] = bname[1]
  finfo['cFREQ'] = bname[2]
  finfo['cYEAR'] = bname[3]
  return finfo
  
def load_nc_var(ffile,cvar,msg=None,dstart=None,dend=None,tinD=None):
  """
  Load netcdf variable to numpy array
  
  Parameters:
  ----------
  ffile : str, netcdf file name 
  cvar: str, variable name 
  dstart,dend (optional) : datetime, start/end time for loading
  tinD,   indexes of time to load (optional), It overrides dstat/dend option 

  Returns:
  -------
  xdata,xtime,msg : np array, with data and xtime with the time 
  msg         : dictionary with messages 
  """
  ctag=ntpath.basename(ffile)+' load var '+cvar 
  if msg is None:
    msg = init_msg()
  msg['Smsg'].append(ctag)
  #if not ntpath.isfile(ffile):
    #print " !! Warning !! File not present !!"
    #msg['Emsg'].append(ctg+"File not present ",ffile)
    #return None,None,msg

  nc = Dataset(ffile,'r')
  try:
    xtime = num2date(nc.variables['time'][:],getattr(nc.variables['time'],'units'))
  except:
    msg['Emsg'].append(ctag+' Could not check time information, check time variable and units attributes')
    nc.close()
    return None,None,msg 
    
  if dstart is None:
    d1 = xtime[0]
  else:
    d1 = dstart
  if dend is None:
    d2 = xtime[-1]
  else:
    d2 = dend
  tind = np.nonzero((xtime >= d1 ) & (xtime <= d2 ))[0]
  if tinD is not None:
    tind = tinD
  if cvar in nc.variables.keys():
    xdata = nc.variables[cvar][tind,:]
    msg['Smsg'].append(ctag+' Ok with dimensions:'+str(xdata.shape))
  else:
    msg['Wmsg'].append(ctag+' Could not find variable, setting to zero!')
    vdims = (len(nc.dimensions['time']),len(nc.dimensions['lat']),len(nc.dimensions['lon']))
    xdata = np.zeros(vdims,dtype='f4')
  nc.close()
  return xdata,xtime[tind],msg
