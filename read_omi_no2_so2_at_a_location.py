#!/usr/bin/python
'''
Module: read_omi_no2_so2_at_a_location.py
==========================================================================================
Disclaimer: The code is for demonstration purposes only. Users are responsible to check for accuracy and revise to fit their objective.

Author: Justin Roberts-Pierel, 2015 
Organization: NASA ARSET
Purpose: To view info about a variety of SDS from an OMI he5 file both generally and at a specific lat/lon

See the README associated with this module for more information.
==========================================================================================
'''

#import necessary modules
import h5py
import numpy as np
import sys
from numpy import unravel_index

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
		# Get lat and lon info
		lat=geolocation['Latitude'][:]
		min_lat=np.min(lat)
		max_lat=np.max(lat)
		lon=geolocation['Longitude'][:]
		min_lon=np.min(lon)
		max_lon=np.max(lon)
		
		#get SDS, or exit program if SDS is not in the file
		try:
			sds=dataFields[SDS_NAME]
		except:
			print('Sorry, your OMI file does not contain the SDS:',SDS_NAME,'. Please try again with the correct file type.')
			continue
		#get scale factor and fill value for data field
		scale=sds.attrs['ScaleFactor']
		fv=sds.attrs['_FillValue']
		mv=sds.attrs['MissingValue']
		offset=sds.attrs['Offset']
		
		#get SDS data
		data=dataFields[SDS_NAME]
		dataArray=data[:].astype(float)
		dataArray[dataArray==float(fv)]=np.nan
		dataArray[dataArray==float(mv)]=np.nan
		dataArray = scale * (dataArray - offset)
		
		#Print the range of latitude and longitude found in the file, then ask for a lat and lon
		print('The range of latitude in this file is: ',min_lat,' to ',max_lat, 'degrees \nThe range of longitude in this file is: ',min_lon, ' to ',max_lon,' degrees')
		user_lat=float(input('\nPlease enter the latitude you would like to analyze (Deg. N): '))
		user_lon=float(input('Please enter the longitude you would like to analyze (Deg. E): '))
		#Continues to ask for lat and lon until the user enters valid values
		while user_lat < min_lat or user_lat > max_lat:
			user_lat=float(input('The latitude you entered is out of range. Please enter a valid latitude: '))
		while user_lon < min_lon or user_lon > max_lon:
			user_lon=float(input('The longitude you entered is out of range. Please enter a valid longitude: '))
			
		#calculation to find nearest point in data to entered location (haversine formula)
		R=6371000#radius of the earth in meters
		lat1=np.radians(user_lat)
		lat2=np.radians(lat)
		delta_lat=np.radians(lat-user_lat)
		delta_lon=np.radians(lon-user_lon)
		a=(np.sin(delta_lat/2))*(np.sin(delta_lat/2))+(np.cos(lat1))*(np.cos(lat2))*(np.sin(delta_lon/2))*(np.sin(delta_lon/2))
		c=2*np.arctan2(np.sqrt(a),np.sqrt(1-a))
		d=R*c
		#gets (and then prints) the x,y location of the nearest point in data to entered location, accounting for no data values
		x,y=np.unravel_index(d.argmin(),d.shape)
		print(x,y)
		print('\nThe nearest pixel to your entered location is at: \nLatitude:',lat[x,y],' Longitude:',lon[x,y])
		if np.isnan(dataArray[x,y]):
			print('The value of ',SDS_NAME,'at this pixel is',fv[0],',(No Value)\n')
		elif dataArray[x,y] != fv:
			print('The value of ', SDS_NAME, 'at this pixel is ',round(dataArray[x,y],3))
			
		#calculates mean, median, stdev in a 3x3 grid around nearest point to entered location
		if x < 1:
			x+=1
		if x > dataArray.shape[0]-2:
			x-=2
		if y < 1:
			y+=1
		if y > dataArray.shape[1]-2:
			y-=2
		three_by_three=dataArray[x-1:x+2,y-1:y+2]
		three_by_three=three_by_three.astype(float)
		three_by_three[three_by_three==float(fv)]=np.nan
		nnan=np.count_nonzero(~np.isnan(three_by_three))
		if nnan == 0:
			print ('There are no valid pixels in a 3x3 grid centered at your entered location.')
		else:
			three_by_three_average=np.nanmean(three_by_three)
			three_by_three_std=np.nanstd(three_by_three)
			three_by_three_median=np.nanmedian(three_by_three)
			if nnan == 1:
				npixels='is'
				mpixels='pixel'
			else:
				npixels='are'
				mpixels='pixels'
			print('There',npixels,nnan,'valid',mpixels,'in a 3x3 grid centered at your entered location.')
			print('The average value in this grid is: ',round(three_by_three_average,3),' \nThe median value in this grid is: ',round(three_by_three_median,3),'\nThe standard deviation in this grid is: ',round(three_by_three_std,3))
		
		#calculates mean, median, stdev in a 5x5 grid around nearest point to entered location
		if x < 2:
			x+=1
		if x > dataArray.shape[0]-3:
			x-=1
		if y < 2:
			y+=1
		if y > dataArray.shape[1]-3:
			y-=1
		five_by_five=dataArray[x-2:x+3,y-2:y+3]
		five_by_five=five_by_five.astype(float)
		five_by_five[five_by_five==float(fv)]=np.nan
		nnan=np.count_nonzero(~np.isnan(five_by_five))
		if nnan == 0:
			print ('There are no valid pixels in a 5x5 grid centered at your entered location. \n')
		else:
			five_by_five_average=np.nanmean(five_by_five)
			five_by_five_std=np.nanstd(five_by_five)
			five_by_five_median=np.nanmedian(five_by_five)
			if nnan == 1:
				npixels='is'
				mpixels='pixel'
			else:
				npixels='are'
				mpixels='pixels'
			print('\nThere',npixels,nnan,' valid',mpixels,' in a 5x5 grid centered at your entered location. \n')
			print('The average value in this grid is: ',round(five_by_five_average,3),' \nThe median value in this grid is: ',round(five_by_five_median,3),'\nThe standard deviation in this grid is: ',round(five_by_five_std,3))