#!/usr/bin/env python

#  General quality control of e2ob simulations 
#
#  Emanuel Dutra, emanuel.dutra@ecmwf.int
#  v1 November 2014 

## general modules to load 
import sys
import os
from netCDF4 import Dataset,num2date
import numpy as np


## list of allowed identifiers:
validD={}
validD['cid']=['ecmwf','univu','metfr','nerc','jrc','cnrs','univk','ambio','csiro','eth']
validD['cver']=['wrr1','wrr2','wrr1_exp1']
validD['cdomain']=['glob30','glob06','eumed30']
validD['cfreq']=['day','mon','1hr','fix']
validD['cvar']=['Precip','Evap','Runoff','Rainf','Qs','Qsb','Qrec','Qsm','PotEvap',
                'ECanop','TVeg','ESoil','EWater','RivOut','Dis','SWnet','LWnet','Qle','Qh',
                'AvgSurfT','Albedo','LAI','SWE','CanopInt','SWEVeg','SurfStor','WaterTableD',
                'SnowFrac','SnowDepth','SurfMoist','RootMoist','TotMoist','GroundMoist',
                'lsm','SurfSoilSat','RootSoilSat','TotSoilSat']
validD['ystart']=range(1979,2013)
validD['yend']=range(1979,2013)
validD['cvar_fix']=['lsm','SurfSoilSat','RootSoilSat','TotSoilSat']


def default_latlon(domain):
  """
  Return the default lat,lon for a certain domain
  
  Parameters:
  ----------
  cdomain: string with the domain info 

  Returns:
  -------
  lat,lon : np array,np.array, with the lat,lon
 
  """
  if domain == "glob30":
    vLON = np.linspace(-179.75,179.75,720)
    vLAT = np.linspace(-89.75,89.75,360)
  else:
    print domain," lat/lon coordinates not coded in default_latlon!"
    sys.exit(-1)
  return vLAT,vLON

def load_nc_var(ffile,cvar,dstart=None,dend=None,tinD=None):
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
  xdata,xtime : np array, with data and xtime with the time 
 
  """
 
  try:
    nc = Dataset(ffile,'r')
  except: 
    print ffile,"\n!! Warning !! Could not open file !!"
    print ffile
    return None,None

  nc = Dataset(ffile,'r')
  try:
    xtime = num2date(nc.variables['time'][:],getattr(nc.variables['time'],'units'))
  except:
    print ffile,'\n Could not check time information, check time variable and units attributes'
    nc.close()
    return None,None
    
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
  else:
    print ffile,'\n Could not find variable'
    return None,None
    nc.close()
  return xdata,xtime[tind]

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


class fname:
  """
  General class to manage e2obs file names

  General attributes:

  """

  def __init__(self):
    self.bstr="e2o"   # default initial tag of each file name 
    self.cid=None     # intitution id
    self.cver=None    # experiment name 
    self.cdomain=None # domain identification
    self.cfreq=None   # temporal frequency 
    self.cvar=None    # variable name contained in the file
    self.ystart=1900  # start year of data 
    self.yend=1900    # end year of data 
    self.cdate="%04i-%04i"%(self.ystart,self.yend)
                      # "YeartStart-YearEnd" information
    self.fname=None   #  file name 
    self.fpath=None        # file name including full path
    self.base="./"    # full path to directoy containing the file 

  def attr2fpath(self,base=None,bstr=None,cid=None,cver=None,
               cdomain=None,cfreq=None,cvar=None,ystart=None,
               yend=None):
    """
    Populate attributes and generate file name from input

    Parameters:
    -----------
    base='./',bstr="e2o",cid=None,cver=None,cdomain=None,
                cfreq=None,cvar=None,ystart=None,yend=None

    Returns:
    instance
    """
    
    # add attr to instance
    for att in ['base','bstr','cid','cver','cdomain',
                 'cfreq','cvar','ystart','yend']:
      if not eval(att+' is None'):
        setattr(self,att,eval(att))
    # derived attributes
    self.cdate="%04i-%04i"%(self.ystart,self.yend)
    if self.cfreq == 'fix':
      self.fname='_'.join([self.bstr,self.cid,self.cver,
                          self.cdomain,self.cfreq,self.cvar])+'.nc'
    else:
      self.fname='_'.join([self.bstr,self.cid,self.cver,
                          self.cdomain,self.cfreq,self.cvar,
                          self.cdate])+'.nc'
    self.fpath=os.path.join(self.base,self.fname)
    return self

  def fpath2attr(self,fpath=None):
    """
    Splits the fpath (full path) into the different components 

    Parameters:
    -----------
    fpath: str, optional (other from instance)

    Returns:
    None, changes the attr of the calling instance 
    """

    if fpath is None:
      fp = self.fpath
    else:
      fp = fpath 

    self.fpath=fp
    self.base=os.path.dirname(self.fpath)
    self.fname=os.path.basename(self.fpath)
    fsplit=self.fname.split('_')
    if len(fsplit) != 7 :
      print "fsplit",len(fsplit)
      raise NameError("fpath2attr: filename does not contain 7 identifiers: "+self.fname)
    self.bstr=fsplit[0]  
    self.cid=fsplit[1]   
    self.cver=fsplit[2]  
    self.cdomain=fsplit[3]
    self.cfreq=fsplit[4]
    self.cvar=fsplit[5]
    self.cdate=fsplit[6][:-3]
    self.ystart=int(fsplit[6][:4])
    self.yend=int(fsplit[6][5:9])
    return self

