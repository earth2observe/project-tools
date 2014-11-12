import csv
import datetime, time
import os, sys
import netCDF4
from stat import S_ISREG, ST_CTIME, ST_MODE

# lat/lon of Penlee Observatory
station_lat   = 50.317993
station_lon   = -4.189128
station_altitude = 8

sourcefolder = 'source_data'
targetfolder = 'output/'
outputfilenameprefix = 'Penlee_Met_simple'

epoch = datetime.datetime.utcfromtimestamp(0)

def csv_to_list(csv_file, delimiter=','):
   with open(csv_file, 'r') as csv_con:
      reader = csv.reader(csv_con, delimiter=delimiter)
      return list(reader)

def append_to_avg_list(avg_list, source_list):
   if len(source_list) > 0:
      return avg_list.append(round(sum(source_list)/len(source_list), 3))

def extract_and_format_data_from_source(sourcefile):
   obs_list = csv_to_list(sourcefile)

   try:
      targetfilename = outputfilenameprefix+'.nc'
      targetfile = targetfolder + targetfilename
   except Exception, e:
      print 'error processing file, skipped: '+ sourcefile
      return

   # to calculate cummulative rain we need to get the last value from the existing netCDF file if it exists
   if os.path.isfile(targetfile):
      # open the netCDF file and get the last value
      rootgrp = netCDF4.Dataset(targetfile, 'a', format='NETCDF4')

      rootgrp.close()

   timestamp = []
   temp = []

   for row in obs_list:
      try:
         # get the timestamp from the first 29 characters in the first column
         ob_timestamp = datetime.datetime.strptime(row[0][0:29],'[%a %b %d %H:%M:%S.%f %Y')
         # get the temperature from column 6, where 6 is the zero-indexed column number in the CSV 
         ob_temp = float(row[6])             

         if isinstance(ob_temp, float):
            timestamp.append((ob_timestamp - epoch).total_seconds())
            temp.append(ob_temp)                      
      except Exception, e:
         print('error in row: ' + str(row) +' in '+ sourcefile)

   # we have the data; next check for an existing file for this datetime
   if os.path.isfile(targetfile):
      # append the data to the file
      rootgrp = netCDF4.Dataset(targetfile, 'a', format='NETCDF4')

      times = rootgrp.variables['time']
      
      start = len(times)
      end = len(times)+len(timestamp)

      times[start:end] = timestamp

      air_temperatures = rootgrp.variables['air_temperature']
      air_temperatures[start:end] = temp

      rootgrp.close()
   else:
      # create a new file and add the data to it
      rootgrp = netCDF4.Dataset(targetfile, 'w', format='NETCDF4')

      # set the global attributes
      rootgrp.id = 'PML-Penlee-Met'
      rootgrp.naming_authority = 'Plymouth Marine Laboratory'
      rootgrp.Metadata_Conventions = 'Unidata Dataset Discovery v1.0'
      rootgrp.Conventions = 'CF-1.6'
      rootgrp.featureType = 'timeSeries'
      # publisher details
      rootgrp.publisher_name = 'Plymouth Marine Laboratory'
      rootgrp.publisher_phone = '+44 (0)1752 633100'
      rootgrp.publisher_url = 'http://www.westernchannelobservatory.org.uk/penlee'
      rootgrp.publisher_email = 'forinfo@pml.ac.uk'
      rootgrp.title = 'Penlee observatory meteorological data'
      rootgrp.summary = 'Air temperature measurements taken at Penlee Point observatory; measurements are taken every 4 seconds.'
      # creator details
      rootgrp.creator_name = 'Ben Calton'
      rootgrp.creator_email = 'bac@pml.ac.uk'
      rootgrp.creator_url = 'https://rsg.pml.ac.uk/'
      
      # create the dimensions
      name_str = rootgrp.createDimension('name_str', 50)
      time = rootgrp.createDimension('time', None)
      
      # create the variables
      station_name = rootgrp.createVariable('station_name', 'c', ('name_str',))
      station_name.cf_role = 'timeseries_id'
      station_name.long_name = 'station name'

      altitude = rootgrp.createVariable('altitude', 'f4', ())
      altitude.standard_name = 'altitude'
      altitude.long_name = 'Observatory altitude'
      altitude.units = 'm'
      
      latitudes = rootgrp.createVariable('lat', 'f4', ())
      latitudes.standard_name = 'latitude'
      latitudes.long_name = 'Observatory latitude'
      latitudes.units = 'degrees_north'

      longitudes = rootgrp.createVariable('lon', 'f4', ())
      longitudes.standard_name = 'longitude'
      longitudes.long_name = 'Observatory longitude'
      longitudes.units = 'degrees_east'

      times = rootgrp.createVariable('time', 'i4', ('time',))
      times.standard_name = 'time'
      times.long_name = 'Time of measurement'
      times.units = 'seconds since 1970-01-01 00:00:00'

      air_temperatures = rootgrp.createVariable('air_temperature', 'f4', ('time',))
      air_temperatures.coordinates = 'lat lon'
      air_temperatures.standard_name = 'air_temperature'
      air_temperatures.long_name = 'Air temperature in degrees Celcius'
      air_temperatures.units = 'degrees Celcius'

      # set the values of the variables
      station_name[:] = netCDF4.stringtoarr('Penlee', 50) 
      altitude[:] = [station_altitude]
      latitudes[:] = [station_lat]
      longitudes[:] = [station_lon]
      times[:] = timestamp
      air_temperatures[:] = temp

      rootgrp.close()

entries = (os.path.join(sourcefolder, fn) for fn in os.listdir(sourcefolder))
entries = ((os.stat(path), path) for path in entries)

# leave only regular files, insert creation date
entries = ((stat[ST_CTIME], path)
           for stat, path in entries if S_ISREG(stat[ST_MODE]))

for cdate, path in sorted(entries):           
  #print('processing '+ path )
  extract_and_format_data_from_source(path)
