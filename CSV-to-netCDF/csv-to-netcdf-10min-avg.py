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
outputfilenameprefix = 'Penlee_Met'

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

   current_ten_min_window = datetime.datetime(1970, 1, 1, 0, 0)
   reading_count = 0
   avg_timestamp = []
   avg_temp = []
   avg_pressure = []
   avg_rh = []
   avg_dewpoint = []
   avg_rainfall_rate = []
   cumulative_rainfall = []
   total_rainfall = 0

   try:
      target_filename_date = datetime.datetime.strptime(obs_list[0][0][0:29],'[%a %b %d %H:%M:%S.%f %Y')
      targetfilename = outputfilenameprefix+'_'+target_filename_date.strftime('%Y%m') +'.nc'
      targetfile = targetfolder + targetfilename
   except Exception, e:
      print 'error processing file, skipped: '+ sourcefile
      return

   # to calculate cummulative rain we need to get the last value from the existing netCDF file if it exists
   if os.path.isfile(targetfile):
      # open the netCDF file and get the last value
      rootgrp = netCDF4.Dataset(targetfile, 'a', format='NETCDF4')

      c_rain = rootgrp.variables['cumulative_rainfall']
      total_rainfall = c_rain[len(c_rain)-1]
      
      rootgrp.close()

   for row in obs_list:
      # get the observation time from the odd format
      ob_timestamp = datetime.datetime.strptime(row[0][0:29],'[%a %b %d %H:%M:%S.%f %Y')
      # round up to the next 10 minute interval, i.e. 10, 20, 30, 40, 50, 00
      ten_min_window_time = ob_timestamp - datetime.timedelta(minutes=ob_timestamp.minute % 10,
                                   seconds=ob_timestamp.second,
                                   microseconds=ob_timestamp.microsecond) + datetime.timedelta(minutes=10)
      
      if ten_min_window_time > current_ten_min_window:
         # ensures that this doesn't run for the first row
         if 'temp' in locals():
            # add the average of all the measurements to the average list 
            avg_timestamp.append((current_ten_min_window - epoch).total_seconds())
            append_to_avg_list(avg_pressure, pressure)
            append_to_avg_list(avg_rh, rh)
            append_to_avg_list(avg_temp, temp)
            append_to_avg_list(avg_dewpoint, dew_point)
            append_to_avg_list(avg_rainfall_rate, rainfall_rate)
            cumulative_rainfall.append(ten_min_rainfall[len(ten_min_rainfall)-1])

         # create/reset the lists for the next 10 minute window
         current_ten_min_window = ten_min_window_time 
         pressure = []
         rh = []
         temp = []
         dew_point = []
         rainfall_rate = []
         ten_min_rainfall = []

         # reset the total_rainfall value if the ten minute window is 00:10; the average is for the previous 10 minutes so this is resetting from midnight
         if ten_min_window_time.hour is 0 and ten_min_window_time.minute is 10:
            total_rainfall = 0

         row_count = 0
      try:
         pressure.append(float(row[4]))
         rh.append(float(row[5]))
         temp.append(float(row[6]))
         dew_point.append(float(row[7]))
         rainfall_rate.append(float(row[11]) * 900)    # sample is every 4 seconds, x 900 to get mm/hr

         total_rainfall = total_rainfall + float(row[11])
         ten_min_rainfall.append(total_rainfall)
         
         row_count = row_count + 1
      except Exception, e:
         print('error in row: ' + str(row) +' in '+ sourcefile)

   # handle the last set of rows; the row count is used to avoid cases where all the rows within a 
   # single ten minute window all have errors
   if row_count > 0:
      avg_timestamp.append((ten_min_window_time - epoch).total_seconds())
      append_to_avg_list(avg_pressure, pressure)
      append_to_avg_list(avg_rh, rh)
      append_to_avg_list(avg_temp, temp)
      append_to_avg_list(avg_dewpoint, dew_point)
      append_to_avg_list(avg_rainfall_rate, rainfall_rate)

      cumulative_rainfall.append(ten_min_rainfall[len(ten_min_rainfall)-1])

   # we have the data; next check for an existing file for this datetime
   if os.path.isfile(targetfile):
      # append the data to the file
      rootgrp = netCDF4.Dataset(targetfile, 'a', format='NETCDF4')

      times = rootgrp.variables['time']
      
      start = len(times)
      end = len(times)+len(avg_timestamp)

      times[start:end] = avg_timestamp

      air_temperatures = rootgrp.variables['air_temperature']
      air_temperatures[start:end] = avg_temp

      air_pressures = rootgrp.variables['air_pressure']
      air_pressures[start:end] = avg_pressure

      relative_humiditys = rootgrp.variables['relative_humidity']
      relative_humiditys[start:end] = avg_rh

      dew_point_temperatures = rootgrp.variables['dew_point_temperature']
      dew_point_temperatures[start:end] = avg_dewpoint

      rain_rate = rootgrp.variables['rainfall_rate']
      rain_rate[start:end] = avg_rainfall_rate

      total_rain = rootgrp.variables['cumulative_rainfall']
      total_rain[start:end] = cumulative_rainfall

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
      rootgrp.summary = 'Air temperature, dew point, pressure and relative humidity measurements taken at Penlee Point observatory. Measurements are taken every 4 seconds and the data in this file is a 10 minute average of each indicator'
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

      air_pressures = rootgrp.createVariable('air_pressure', 'f4', ('time',))
      air_pressures.coordinates = 'lat lon'
      air_pressures.standard_name = 'air_pressure'
      air_pressures.long_name = 'Air pressure'
      air_pressures.units = 'millibars'

      relative_humiditys = rootgrp.createVariable('relative_humidity', 'f4', ('time',))
      relative_humiditys.coordinates = 'lat lon'
      relative_humiditys.standard_name = 'relative_humidity'
      relative_humiditys.long_name = 'Relative humidity'
      relative_humiditys.units = '%'

      dew_point_temperatures = rootgrp.createVariable('dew_point_temperature', 'f4', ('time',))
      dew_point_temperatures.coordinates = 'lat lon'
      dew_point_temperatures.standard_name = 'dew_point_temperature'
      dew_point_temperatures.long_name = 'Dew point temperature'
      dew_point_temperatures.units = 'degrees Celcius'

      rain_rate = rootgrp.createVariable('rainfall_rate', 'f4', ('time',))
      rain_rate.coordinates = 'lat lon'
      rain_rate.standard_name = 'rainfall_rate'
      rain_rate.long_name = 'Rainfall rate'
      rain_rate.units = 'mm hr-1'

      total_rain = rootgrp.createVariable('cumulative_rainfall', 'f4', ('time',))
      total_rain.coordinates = 'lat lon'
      total_rain.standard_name = 'cumulative_rainfall'
      total_rain.long_name = 'Cumulative rainfall'
      total_rain.units = 'mm'

      # set the values of the variables
      station_name[:] = netCDF4.stringtoarr('Penlee', 50) 
      altitude[:] = [station_altitude]
      latitudes[:] = [station_lat]
      longitudes[:] = [station_lon]
      times[:] = avg_timestamp
      air_temperatures[:] = avg_temp
      air_pressures[:] = avg_pressure
      relative_humiditys[:] = avg_rh
      dew_point_temperatures[:] = avg_dewpoint
      rain_rate[:] = avg_rainfall_rate
      total_rain[:] = cumulative_rainfall

      rootgrp.close()

entries = (os.path.join(sourcefolder, fn) for fn in os.listdir(sourcefolder))
entries = ((os.stat(path), path) for path in entries)

# leave only regular files, insert creation date
entries = ((stat[ST_CTIME], path)
           for stat, path in entries if S_ISREG(stat[ST_MODE]))

for cdate, path in sorted(entries):           
  #print('processing '+ path )
  extract_and_format_data_from_source(path)
