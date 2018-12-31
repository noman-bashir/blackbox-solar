from datetime import timedelta, datetime
import pandas as pd
import pvlib
from tzwhere import tzwhere
import datetime
import pytz

latitude = 42.2504556
longitude = -72.6787206 

start_time = '12/31/15 0:00'
end_time = '12/31/15 23:00'

#calculate the timezone of the given latitude and longitude
tz = tzwhere.tzwhere()
timezone_str = tz.tzNameAt(latitude, longitude)
# timezone_str

global timezone
timezone = pytz.timezone(timezone_str)

#obtaining the clear sky solar generation for the given latitude and longitude for the given start and end time
timedelta_index = pd.date_range(start=start_time, end=end_time, freq='H', tz=timezone).to_series()

for index, value in timedelta_index.iteritems():
    dt = index.to_pydatetime()
    solpos = pvlib.solarposition.get_solarposition(dt, latitude, longitude)
    print(solpos)



    