from __future__ import division
from helpers import parameters
from pvlib.location import Location
from pysolar.solar import * 
from tzwhere import tzwhere

import sys
import pandas as pd
import datetime
import pytz
import numpy as np


# import os
# import datetime as dt


# import csv
# import pytz
# import datetime
# import matplotlib
# import sys , getopt
# from math import sqrt
# from sklearn import metrics
# import matplotlib.pyplot as plt
# from sklearn.metrics import mean_squared_error
# from pvlib import clearsky, atmosphere, solarposition
# from pvlib.tools import datetime_to_djd, djd_to_datetime


#converting the arguments to float
latitude = float(sys.argv[1])
longitude = float(sys.argv[2])

#reading the data.csv file into a pandas dataframe
df = pd.read_csv(sys.argv[3], delimiter=',')

#reverseing 
df.iloc[:] = df.iloc[::-1].values

#obatin the start and end time 
length = len(df) - 1 
start_time = df['Date & Time'][0]
end_time = df['Date & Time'][length]

#calculate the timezone of the given latitude and longitude
tz = tzwhere.tzwhere()
timezone_str = tz.tzNameAt(latitude, longitude)
# timezone_str

global timezone
timezone = pytz.timezone(timezone_str)

#obtaining the clear sky solar generation for the given latitude and longitude for the given start and end time
timedelta_index = pd.date_range(start=start_time, end=end_time, freq='H', tz=timezone).to_series()

time = []
irradiance = []
for index, value in timedelta_index.iteritems():
    dt = index.to_pydatetime()
    altitude_deg = get_altitude(latitude, longitude, dt)
    clear_sky = radiation.get_radiation_direct(dt, altitude_deg)
    irradiance.append(clear_sky)
    time.append(dt)

cs = pd.DataFrame(np.column_stack([time, irradiance]),columns=['time', 'ghi'])

initial_k = 100
initial_surface_azimuth = 3.1415
initial_surface_tilt = 0.737409

time_clearsky_gen = pd.concat([cs, df[['Generation [kW]', 'Ambient Temp [°c]']]], axis=1)

#calling the parameter function to get the optimised values of k, orientaion and tilt values
final =  parameters(initial_k, initial_surface_azimuth, initial_surface_tilt, latitude, longitude, time_clearsky_gen)

print(final)
# #obtain the index value of calculated data which has the minimum differnce with the solar generation data 
# s_data = final[3]
# s_clean_data = []
# for x in s_data:
#     if ( x != 0.0 and x != -0.0 ):
#         s_clean_data.append(x)
        
# s_clean_data_length = len(s_clean_data) - 1

# s_data_clean_first_index = s_data.index(s_clean_data[0]) 
# s_data_clean_last_index = s_data.index(s_clean_data[s_clean_data_length])
# s_af = af[s_data_clean_first_index:s_data_clean_last_index]
    
# diff_list = []
# for d,g in zip(s_clean_data , s_af):
#     if(d > g):
#         diff = d - g
#         diff_list.append(diff)
#     else:
#         diff = g - d
#         diff_list.append(diff)
   

# minimum_diff = min(diff_list)
# minimum_diff_index = diff_list.index(minimum_diff) + s_data_clean_first_index
# #print(diff_list)





# para = parameters_k_adjusted (final[0],final[1],final[2])

# #the value of k
# k = para[0]
# print("The value of K is :" , k)

# #the value of orientation in degress by multiplying it with 57.296
# orientation = para[1] * 57.296
# print("The value of orientation is :" , orientation)

# #the value of tilt in degress by multiplying it with 57.296
# surface_tilt = para[2] * 57.296
# print("The value of surface_tilt is :" , surface_tilt)

# #the value of c
# c = para[4]
# print("The value of c is :" , c)
