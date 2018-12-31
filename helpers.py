from pvlib import atmosphere
import pvlib
import pandas as pd
import math
import os
import pytz
import numpy as np
from tzwhere import tzwhere
from importlib import reload
import datetime
from sklearn import metrics

def parameter_K(clear_sky, gen_data, z, surface_tilt, surface_azimuth, azimuth, zenith):

    k = z

    gen_data = gen_data * 1000

    solar_data = clear_sky * k * ( math.cos(1.5708-zenith) * math.sin(surface_tilt) * math.cos(surface_azimuth - azimuth) + math.sin(1.5708-zenith) * math.cos(surface_tilt))

    solar_data = 0 if solar_data < 1 else solar_data
    # defining error as 1% of generation data
    if (solar_data > 0): 
        while (abs(solar_data-gen_data) > 0.01 * gen_data):
            if (solar_data > gen_data):
                k = k/2
                solar_data = clear_sky * k * ( math.cos(1.5708-zenith) * math.sin(surface_tilt) * math.cos(surface_azimuth - azimuth) + math.sin(1.5708-zenith) * math.cos(surface_tilt))
            else:
                k = k+0.01
                solar_data = clear_sky * k * ( math.cos(1.5708-zenith) * math.sin(surface_tilt) * math.cos(surface_azimuth - azimuth) + math.sin(1.5708-zenith) * math.cos(surface_tilt))
    else:
        k = 0

    print(k, solar_data, gen_data)

    return k

def parameter_azimuth(clear_sky, gen_data, new_k, surface_tilt, surface_azimuth, azimuth, zenith):

    solar_data = 0
    perfect_surface_azimuth = surface_azimuth
    new_surface_azimuth = surface_azimuth
    new_solar_data = 0

    #vary the value of azimuth from 0 degrees to 360 degrees to obtain the one which gives tightest bound on data
    for i in np.arange(0, 6.28319, 0.08727):
        
        #copy of older azimuth and its data values
        surface_azimuth = i
        old_solar_data = new_solar_data
        
        old_surface_azimuth = new_surface_azimuth
        
        solar_data = clear_sky * new_k * ( math.cos(1.5708-zenith) * math.sin(surface_tilt) * math.cos(surface_azimuth - azimuth) + math.sin(1.5708-zenith) * math.cos(surface_tilt))
        
        #copy of new azimuth and its data values
        new_solar_data = solar_data
        new_surface_azimuth = surface_azimuth

        #discard the values if it is outside the bound i.e above clear sky and solar generation
        if (solar_data < gen_data):
            continue
        elif (solar_data > clear_sky):
            continue
        else:
            #inside the bound obtain the one which gives tightest bound on data
            if(new_solar_data < old_solar_data):
                perfect_surface_azimuth = old_surface_azimuth
            else:
                perfect_surface_azimuth = new_surface_azimuth
            
    return perfect_surface_azimuth

def parameter_tilt(clear_sky, gen_data,new_k,surface_tilt, surface_azimuth, azimuth, zenith):

    solar_data = 0
    perfect_surface_tilt = surface_tilt
    new_surface_tilt = surface_tilt
    new_solar_data = 0
    
    #vary the value of tilt from 0 degrees to 90 degrees to obtain the one which gives tightest bound on data
    for i in np.arange(0, 1.5708, 0.08727):
        
        surface_azimuth = i
        
        #copy of older tilt and its data values
        old_solar_data = new_solar_data
        
        old_surface_tilt = new_surface_tilt
        
        solar_data = clear_sky * new_k * ( math.cos(1.5708-zenith) * math.sin(surface_tilt) * math.cos(surface_azimuth - azimuth) + math.sin(1.5708-zenith) * math.cos(surface_tilt))
        
        #copy of new tilt and its data values
        new_solar_data = solar_data
        new_surface_tilt = surface_tilt

        #discard the values if it is outside the bound i.e above clear sky and solar generation
        if (solar_data < gen_data):
            continue
        elif (solar_data > clear_sky):
            continue
        else:
            #inside the bound obtain the one which gives tightest bound on data
            if(new_solar_data < old_solar_data):
                perfect_surface_tilt = new_surface_tilt
            else:
                perfect_surface_tilt = old_surface_tilt
            
    return perfect_surface_tilt

def parameters(k_init, surface_azimuth_init, surface_tilt_init, latitude, longitude, time_clearsky_gen):
    gen_data = []
    data = []
    rmse = []
    k_list = []
    sa_list = []
    st_list = []
    clean_data = []

    for _ , row in time_clearsky_gen.iterrows():

        # getting data for that time and location
        solar_position_data = pvlib.solarposition.get_solarposition(row['time'], latitude, longitude)

        #conerting the azimuth and zenith angles from degrees to radians
        azimuth = math.radians(solar_position_data['azimuth'])
        zenith = math.radians(solar_position_data['zenith'])

        # obtain all the solar generation values in a list
        gen_data.append(row['Generation [kW]'])

        #call the parameter_k function to get the optimised value of k
        optimised_k = parameter_K(row['ghi'], row['Generation [kW]'], k_init, surface_tilt_init, surface_azimuth_init, azimuth, zenith)
        k_list.append(optimised_k)
       
        #call the parameter_azimuth function to get the optimised value of surface azimuth(orientaion)
        optimised_surface_azimuth = parameter_azimuth(row['ghi'], row['Generation [kW]'], optimised_k, surface_tilt_init, surface_azimuth_init, azimuth, zenith)
        sa_list.append(optimised_surface_azimuth)

        #call the parameter_tilt function to get the optimised value of surface tilt
        optimised_surface_tilt = parameter_tilt(row['ghi'], row['Generation [kW]'], optimised_k, surface_tilt_init, optimised_surface_azimuth, azimuth, zenith)
        st_list.append(optimised_surface_tilt)

        #calculate the solar data for the optimised values of k, orientaion and tilt
        solar_data = row['ghi'] * optimised_k * ( math.cos(1.5708-zenith) * math.sin(optimised_surface_tilt) * math.cos(optimised_surface_azimuth - azimuth) + math.sin(1.5708-zenith) * math.cos(optimised_surface_tilt))
        data.append(solar_data)

        #discard the values if it is 0 as they will affect the rmse value
        if (solar_data != 0 and solar_data != -0.0):
            clean_data.append(solar_data)
        
        #calculate the rmse for non zero values    
        rmse_data = np.sqrt(metrics.mean_squared_error(gen_data, data))
        rmse.append(rmse_data)
        # print(optimised_k, solar_data, row['Generation [kW]']*1000)
     
    clean_data_length = len(clean_data) - 1

    data_clean_first_index = data.index(clean_data[0])
    data_clean_last_index = data.index(clean_data[clean_data_length])
    
    minimum_rmse = min(rmse[data_clean_first_index : data_clean_last_index])
    index_rmse = rmse.index(minimum_rmse)

    #obtain the values of k, orientaion and tilt values for which we get minimum rmse
    next_k = k_list[index_rmse]
    next_surface_azimuth = sa_list[index_rmse]
    next_surface_tilt = st_list[index_rmse]
    
    return (next_k, next_surface_azimuth, next_surface_tilt)



#     def parameter_k_adjust(clear_sky, gen_data,optimised_k, optimised_surface_azimuth, optimised_surface_tilt, Tbase, Tair):
    
#     global c
#     c_list = []
#     azimuth = 2.05819
#     zenith = 1.639965
#     solar_data = 0
#     perfect_k_adjust = 0
#     new_k_adjust = 0
#     new_solar_data = 0
    
#     #calculating the value of c for wich it eives the tightest upper bound
#     for i in np.arange(0, 0.5, 0.001):
        
#         c = i
#         old_solar_data = new_solar_data
        
#         old_k_adjust = new_k_adjust
        
#         #calculate the adjusted k for the varying c
#         k_adjust = optimised_k * (1 + c * ( Tbase - Tair))

#         solar_data = clear_sky * k_adjust * ( math.cos(1.5708-zenith) * math.sin(optimised_surface_tilt) * math.cos(optimised_surface_azimuth - azimuth) + math.sin(1.5708-zenith) * math.cos(optimised_surface_tilt))
        
#         new_solar_data = solar_data
#         new_k_adjust = k_adjust

#         if (solar_data < gen_data):
#             continue
#         elif (solar_data > clear_sky):
#             continue
#         else:
#             if(new_solar_data < old_solar_data):
#                 perfect_k_adjust = new_k_adjust
#             else:
#                 perfect_k_adjust = old_k_adjust
    
#     return (perfect_k_adjust)


# def parameters_k_adjusted (k, surface_azimuth, surface_tilt):
#     gen_data = []
#     data = []
#     rmse = []
#     k_list = []
#     sa_list = []
#     st_list = []
#     clean_data = []
#     Tair = []
#     Tair = tf

#     Tbase = Tair[minimum_diff_index]
#     for x,y,t in zip(bf,af,Tair):
        
#         gen_data.append(y)
        
#         Tair = t

#         #obtain the temperature adjusted value of k
#         adjusted_k = parameter_k_adjust(x,y,k, surface_azimuth,surface_tilt, Tbase, Tair)
#         k_list.append(adjusted_k)
        
#         #calculate the solar data based on the adjusted k 
#         solar_data = x * adjusted_k * ( math.cos(1.5708-zenith) * math.sin(surface_tilt) * math.cos(surface_azimuth - azimuth) + math.sin(1.5708-zenith) * math.cos(surface_tilt))
#         data.append(solar_data)

#         if (solar_data != 0 and solar_data != -0.0):
#             clean_data.append(solar_data)
        
#         #calculate the rmse for non zero values    
#         rmse_data = np.sqrt(metrics.mean_squared_error(gen_data, data))
#         rmse.append(rmse_data)
    
#     clean_data_length = len(clean_data) - 1

#     data_clean_first_index = data.index(clean_data[0])
#     data_clean_last_index = data.index(clean_data[clean_data_length])
    
#     minimum_rmse = min(rmse)
#     index_rmse = rmse.index(minimum_rmse) + data_clean_first_index

#     #obtain the values of k, orientaion and tilt values for which we get minimum rmse
#     next_k = k_list[index_rmse]
   
#     return (next_k, surface_azimuth, surface_tilt,data,c)