#!/usr/bin/python
'''
Module: read_and_map_omi_no2_so2.py
==========================================================================================
Disclaimer: The code is for demonstration purposes only. Users are responsible to check for accuracy and revise to fit their objective.

Author: Justin Roberts-Pierel, 2015 
Organization: NASA ARSET
Purpose: To extract No2 or SO2 data from an OMI HDF5 file and create a map of the resulting data

See the README associated with this module for more information.
==========================================================================================
'''

import h5py
import numpy as np
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
import sys

#This finds the user's current path so that all hdf4 files can be found
try:
	fileList=open('fileList.txt','r')
except:
	print('Did not find a text file containing file names (perhaps name does not match)')
	sys.exit()

#loops through all files listed in the text file
for FILE_NAME in fileList:
	FILE_NAME=FILE_NAME.strip()
	user_input=input('\nWould you like to process\n' + FILE_NAME + '\n\n(Y/N)')
	if(user_input == 'N' or user_input == 'n'):
		print('Skipping...')
		continue
	else:
		file = h5py.File(FILE_NAME, 'r')   # 'r' means that hdf5 file is open in read-only mode
		#checks if the file contains NO2 or SO2 data, and reacts accordingly
		if 'NO2' in FILE_NAME:
			print('This is an OMI NO2 file. Here is some information: ')
			#this is how you access the data tree in an hdf5 file
			dataFields=file['HDFEOS']['SWATHS']['ColumnAmountNO2']['Data Fields']
			geolocation=file['HDFEOS']['SWATHS']['ColumnAmountNO2']['Geolocation Fields']
			SDS_NAME='ColumnAmountNO2'
			data=dataFields[SDS_NAME]
			map_label=data.attrs['Units'].decode()
		elif 'SO2' in FILE_NAME:
			print('This is an OMI SO2 file. Here is some information: ')
			dataFields=file['HDFEOS']['SWATHS']['OMI Total Column Amount SO2']['Data Fields']
			geolocation=file['HDFEOS']['SWATHS']['OMI Total Column Amount SO2']['Geolocation Fields']
			SDS_NAME='ColumnAmountSO2_PBL'
			data=dataFields[SDS_NAME]
			valid_min=data.attrs['ValidRange'][0]
			valid_max=data.attrs['ValidRange'][1]
			map_label=data.attrs['Units'].decode()
			print('Valid Range is: ',valid_min,valid_max)
		else:
			print('The file named :',FILE_NAME, ' is not a valid OMI file. \n')
			#if the program is unable to determine that it is an OMI SO2 or NO2 file, then it will skip to the next file
			continue
			
		#get necessary attributes 
		fv=data.attrs['_FillValue']
		mv=data.attrs['MissingValue']
		offset=data.attrs['Offset']
		scale=data.attrs['ScaleFactor']
		
		#get lat and lon information 
		lat=geolocation['Latitude'][:]
		min_lat=np.min(lat)
		max_lat=np.max(lat)
		lon=geolocation['Longitude'][:]
		min_lon=np.min(lon)
		max_lon=np.max(lon)
		
		#get the data as an array and mask fill/missing values
		dataArray=data[:]
		dataArray[dataArray==fv]=np.nan
		dataArray[dataArray==mv]=np.nan
		dataArray = scale * (dataArray - offset)
		
		#get statistics about data
		average=np.nanmean(dataArray)
		print(average)
		stdev=np.nanstd(dataArray)
		median=np.nanmedian(dataArray)
		
		#print statistics 
		print('The average of this data is: ',round(average,3),'\nThe standard deviation is: ',round(stdev,3),'\nThe median is: ',round(median,3))
		print('The range of latitude in this file is: ',min_lat,' to ',max_lat, 'degrees \nThe range of longitude in this file is: ',min_lon, ' to ',max_lon,' degrees')
		is_map=input('\nWould you like to create a map of this data? Please enter Y or N \n')
		
		#if user would like a map, view it
		if is_map == 'Y' or is_map == 'y':
			data = np.ma.masked_array(data, np.isnan(data))
			m = Basemap(projection='cyl', resolution='l',
						llcrnrlat=-90, urcrnrlat = 90,
						llcrnrlon=-180, urcrnrlon = 180)
			m.drawcoastlines(linewidth=0.5)
			m.drawparallels(np.arange(-90., 120., 30.), labels=[1, 0, 0, 0])
			m.drawmeridians(np.arange(-180, 180., 45.), labels=[0, 0, 0, 1])
			my_cmap = plt.cm.get_cmap('gist_stern_r')
			my_cmap.set_under('w')
			m.pcolormesh(lon, lat, data, latlon=True, vmin=0, vmax=np.nanmax(data)*.35,cmap=my_cmap)
			cb = m.colorbar()
			cb.set_label(map_label)
			plt.autoscale()
			#title the plot
			plt.title('{0}\n {1}'.format(FILE_NAME, SDS_NAME))
			fig = plt.gcf()
			# Show the plot window.
			plt.show()
		#once you close the map it asks if you'd like to save it
			is_save=str(input('\nWould you like to save this map? Please enter Y or N \n'))
			if is_save == 'Y' or is_save == 'y':
				#saves as a png if the user would like
				pngfile = '{0}.png'.format(FILE_NAME[:-3])
				fig.savefig(pngfile)
		#close the hdf5 file 
		file.close()