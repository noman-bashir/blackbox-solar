from __future__ import division
from helpers import parameters
from pvlib.location import Location
from pysolar.solar import * 
from tzwhere import tzwhere
from darksky import forecast 
from time import sleep

import requests
import sys
import pandas as pd
import datetime
import pytz
import numpy as np
import pvlib

key = "412ebd14d07bb02304337b56bee48a03" # informal gmail

#converting the arguments to float
latitude = float(sys.argv[1])
longitude = float(sys.argv[2])

LOCATION = key, latitude, longitude

#reading the data.csv file into a pandas dataframe
df = pd.read_csv(sys.argv[3], delimiter=',')

#reverseing 
df.iloc[:] = df.iloc[::-1].values

# #obatin the start and end time 
# start_time = datetime.datetime(year = 2015, month = 1, day = 1, hour = 0, minute = 0, second = 0)
# end_time = datetime.datetime(year = 2015, month = 12, day = 31, hour = 23, minute = 0, second = 0)

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
timedelta_index = pd.date_range(start=start_time, end=end_time, freq='1H', tz=timezone).to_series()

# print(timedelta_index)

time = []
irradiance = []
sun_azimuth = []
sun_zenith = []
for index, value in timedelta_index.iteritems():

    dt = index.to_pydatetime()

    altitude_deg = get_altitude(latitude, longitude, dt)
    clear_sky = radiation.get_radiation_direct(dt, altitude_deg)

    irradiance.append(clear_sky)
    time.append(dt)

    # getting data for that time and location
    solar_position_data = pvlib.solarposition.get_solarposition(dt, latitude, longitude)

    #conerting the azimuth and zenith angles from degrees to radians
    azimuth = math.radians(solar_position_data['azimuth'])
    zenith = math.radians(solar_position_data['zenith'])

    # append azimuth and zenith
    sun_azimuth.append(azimuth)
    sun_zenith.append(zenith)

    print(dt)

cs = pd.DataFrame(np.column_stack([time, irradiance, sun_azimuth, sun_zenith]),columns=['time', 'clearsky', 'azimuth', 'zenith'])

df['solar'] = df['Generation [kW]'] * 1000

input_data = pd.concat([cs, df['solar']], axis=1)


input_data['time'] = input_data['time'].apply(lambda x:(datetime.datetime.date(x)))

cloudcover = []
temperature = []
for day in input_data['time'].drop_duplicates():
    day = datetime.datetime(day.year, day.month, day.day)
    print(day)
    try:
        location = forecast(*LOCATION, time = day.isoformat())
        # cloud = [hour.cloudCover for hour in location.hourly[:]]
        temp = [hour.temperature for hour in location.hourly[:]]
        for i in range(len(temp)):
            # cloudcover.append(cloud[i])
            temperature.append(temp[i])
    except requests.exceptions.HTTPError as e:
        print(e)
        pass
    sleep(0.1)

print(len(cloudcover), len(temperature), len(input_data))

tmp1 = pd.Series(temperature)
# tmp2 = pd.Series(cloudcover)

input_data['temp'] = tmp1.values
# input_data['cloudcover'] = tmp2.values

input_data = input_data[input_data.solar>0]


input_data = input_data.groupby('time', as_index=False).apply(lambda group: group.iloc[1:]).reset_index()
input_data = input_data.drop(['level_0', 'level_1'], axis = 1)
input_data = input_data.groupby('time', as_index=False).apply(lambda group: group.iloc[:-1]).reset_index()
input_data = input_data.drop(['level_0', 'level_1'], axis = 1)

input_data.to_csv('data.csv', index=False)
