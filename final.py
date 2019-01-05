from __future__ import division
from helpers import parameters

import pandas as pd


#reading the data.csv file into a pandas dataframe
df = pd.read_csv('data.csv', delimiter=',')

print(df)

#calling the parameter function to get the optimised values of k, orientaion and tilt values
# final = parameters(initial_k, initial_surface_azimuth, initial_surface_tilt, input_data)

# #the value of k
# print("The value of K is :" , final[0])

# #the value of orientation in degress by multiplying it with 57.296
# print("The value of orientation is :" , math.degrees(final[1]))

# #the value of tilt in degress by multiplying it with 57.296
# print("The value of surface_tilt is :" , math.degrees(final[2]))