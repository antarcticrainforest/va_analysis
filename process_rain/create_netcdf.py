#!/usr/bin/env python2.7

from netCDF4 import Dataset as nc
from netCDF4 import date2num
import numpy as np
from datetime import datetime
import sys,os,re

def getlon(c,dw):
    R=6370.9989
    return c + (dw/(R*np.cos(c*np.pi/180.)) * 180./np.pi)

def getlat(c,dw):
    R=6370.9989
    return c + (dw/R * 180./np.pi)

try:
    infile=sys.argv[1]
    outfile=sys.argv[2]
except IndexError:
    sys.exit('Error: \n Usage: %s infile.nc outfile.nc' %sys.argv[0])
try:
    head=sys.argv[3]
except IndexError:
    fn = os.path.basename(infile).replace('.nc','').replace('.nc4','').replace('-','_')
    #head = fn.replace(re.search(r'\d{8}_\d{4}', fn).group(),'')
    head = fn.replace(re.search(r'\d{8}_level2', fn).group(),'')

#Get the working directory
dirname=os.path.dirname(os.path.abspath(infile))

#Open the infile and outfile
if not os.path.isfile(infile):
    sys.stderr.write("%s is missing"%infile)

units='seconds since 1970-01-01 00:00:00Z'
with nc(infile,'r') as s:
    with nc(outfile,'w') as t:
        #Create the header of the outfile
        try:
            t.createDimension('i',len(s.dimensions['y']))
            t.createDimension('lat',len(s.dimensions['y']))
        except KeyError:
            t.createDimension('i',len(s.dimensions['i']))
            t.createDimension('lat',len(s.dimensions['i']))
        try:
            t.createDimension('lon',len(s.dimensions['x']))
            t.createDimension('j',len(s.dimensions['x']))
        except KeyError:
            t.createDimension('lon',len(s.dimensions['j']))
            t.createDimension('j',len(s.dimensions['j']))

        t.createDimension('time',None)

        t.createVariable('lon','f',('i','j'))
        t.createVariable('lat','f',('i','j'))
        t.createVariable('i','f',('i',))
        t.createVariable('j','f',('j',))
        t.createVariable('time','i',('time',))
        t.createVariable('rain_rate','f',('time','i','j'),fill_value=-99.99)

        t.variables['lat'].units='degrees_north'
        t.variables['lat'].long_name='latitude'
        t.variables['lon'].units='degrees_east'
        t.variables['lon'].long_name='longitude'

        t.variables['i'].units='degrees_north'
        t.variables['i'].long_name='latitude'
        t.variables['j'].units='degrees_east'
        t.variables['j'].long_name='longitude'



        t.variables['time'].long_name='time of radar scan'
        t.variables['time'].units=units
        t.variables['rain_rate'].long_name='rain rate'
        t.variables['rain_rate'].units='mm/hr'
        t.variables['rain_rate'].missing_value=-99.99

        #Assign the values, start with lon-lat
        #Get the center of the radar-station first
        try:
            center=(s.variables['radar_latitude'][:],s.variables['radar_longitude'][:])
        except KeyError:
            center=(-12.24919987,131.04440308)
        #Get the width of the radar and the corresponding lon/lats
        try:
            xw=(s.variables['x'][0],s.variables['x'][-1])
            lon=np.flipud(np.array([getlon(center[1],d) for d in s.variables['x'][:]]))
        except KeyError:
            xw=(s.variables['j'][0],s.variables['j'][-1])
            lon=np.flipud(np.array([getlon(center[1],d) for d in s.variables['j'][:]]))
        try:
            yw=(s.variables['y'][0],s.variables['y'][-1])
            lat=np.array([getlat(center[0],d) for d in s.variables['y'][:]])
        except KeyError:
            yw=(s.variables['i'][0],s.variables['i'][-1])
            lat=np.array([getlat(center[0],d) for d in s.variables['i'][:]])
        Y,X=np.meshgrid(lat,lon)

        #Get the time 
        #print('seltsamer name',os.path.join(dirname)+'CPOL'+'%Y%m%d_%H%M'*+'.nc')
        #time=datetime.strptime(infile,os.path.join(dirname)+'/'+'CPOL_'+'%Y%m%d_%H%M'+'_GRIDS_2500m.nc')
        time=datetime.strptime(infile,os.path.join(dirname,head)+'%Y%m%d_level2.nc')

        index=date2num(time,units)

        #Get the rain rate data
        for varname in ('rr','rain_rate','radar_estimated_rain_rate'):
            try:
                rr = s.variables[varname][:]
                break
            except KeyError:
                pass
        #Assign all
        t.variables['lat'][:]=Y
        t.variables['lon'][:]=X
        t.variables['i'][:]=lat
        t.variables['j'][:]=lon
        t.variables['time'][:]=index
        t.variables['rain_rate'][:]=rr
print '%s: created %s' %(sys.argv[0],outfile)
