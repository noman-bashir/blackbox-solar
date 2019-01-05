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

def parameter_K(k, surface_tilt, surface_azimuth, data):
    print(data['zenith']*data['zenith'])
    # print(math.cos(data['zenith']))

    # solar_data = clear_sky * k * ( math.cos(math.radians(90)-zenith) * math.sin(surface_tilt) * math.cos(surface_azimuth - azimuth) + math.sin(math.radians(90)-zenith) * math.cos(surface_tilt))

    # solar_data = 0 if solar_data < 1 else solar_data

    # # defining error as 1% of generation data
    # if (solar_data > 0): 
    #     while (abs(solar_data-gen_data) > 0.001 * gen_data):
    #         if (solar_data > gen_data):
    #             k = k/2
    #             solar_data = clear_sky * k * ( math.cos(math.radians(90)-zenith) * math.sin(surface_tilt) * math.cos(surface_azimuth - azimuth) + math.sin(math.radians(90)-zenith) * math.cos(surface_tilt))
    #         else:
    #             k = k + 0.01
    #             solar_data = clear_sky * k * ( math.cos(math.radians(90)-zenith) * math.sin(surface_tilt) * math.cos(surface_azimuth - azimuth) + math.sin(math.radians(90)-zenith) * math.cos(surface_tilt))
    #     while (solar_data < gen_data):
    #         k = k + 0.0001
    #         solar_data = clear_sky * k * ( math.cos(math.radians(90)-zenith) * math.sin(surface_tilt) * math.cos(surface_azimuth - azimuth) + math.sin(math.radians(90)-zenith) * math.cos(surface_tilt))
    # else:
    #     k = 100

    return k

def parameter_azimuth(clear_sky, gen_data, new_k, surface_tilt, surface_azimuth, azimuth, zenith):

    return_val = surface_azimuth
    df = pd.DataFrame(columns=['azimuth', 'solar_data', 'gen_data', 'diff'])

    gen_data = gen_data * 1000

    #vary the value of azimuth from 0 degrees to 360 degrees to obtain the one which gives tightest bound on data
    for i in np.arange(0, 2*math.pi, math.radians(1)):
        
        #copy of older azimuth and its data values
        surface_azimuth = i
        
        solar_data = clear_sky * new_k * (math.cos(math.radians(90)-zenith) * math.sin(surface_tilt) * math.cos(surface_azimuth - azimuth) + math.sin(math.radians(90)-zenith) * math.cos(surface_tilt))
        
        df = df.append({'azimuth': i, 'solar_data': solar_data, 'gen_data': gen_data, 'diff':(solar_data-gen_data) }, ignore_index=True)

    if clear_sky > 0:            
        try:
            df = df.loc[df['solar_data'] >= df['gen_data']]
            min_val_row = df.ix[df['solar_data'].idxmin()]
            return_val = min_val_row['azimuth']
        except ValueError as e:
            pass

    return return_val
    # min_val_row['azimuth']


def parameter_tilt(clear_sky, gen_data,new_k,surface_tilt, surface_azimuth, azimuth, zenith):
    
    df = pd.DataFrame(columns=['tilt', 'diff'])

    gen_data = gen_data * 1000

    #vary the value of azimuth from 0 degrees to 360 degrees to obtain the one which gives tightest bound on data
    for i in np.arange(0, 2*math.pi, math.radians(1)):

        
        #copy of older azimuth and its data values
        surface_tilt = i
        
        solar_data = clear_sky * new_k * (math.cos(math.radians(90)-zenith) * math.sin(surface_tilt) * math.cos(surface_azimuth - azimuth) + math.sin(math.radians(90)-zenith) * math.cos(surface_tilt))

        df = df.append({'tilt': i, 'diff': abs(solar_data-gen_data) }, ignore_index=True)

    min_val_row = df.ix[df['diff'].idxmin()]

    return min_val_row['tilt']



def parameters(k_init, surface_azimuth_init, surface_tilt_init, data):

    #call the parameter_k function to get the optimised value of k
    optimised_k = parameter_K(k_init, surface_tilt_init, surface_azimuth_init, data)

    # para = pd.DataFrame(columns=['k', 'surface_azimuth', 'surface_tilt', 'sun_azimuth', 'sun_zenith'])

    # for _ , row in time_clearsky_gen.iterrows():

    #     # getting data for that time and location
    #     solar_position_data = pvlib.solarposition.get_solarposition(row['time'], latitude, longitude)

    #     #conerting the azimuth and zenith angles from degrees to radians
    #     azimuth = math.radians(solar_position_data['azimuth'])
    #     zenith = math.radians(solar_position_data['zenith'])

    #     #call the parameter_k function to get the optimised value of k
    #     optimised_k = parameter_K(row['ghi'], row['Generation [kW]'], k_init, surface_tilt_init, surface_azimuth_init, azimuth, zenith)
       
    #     #call the parameter_azimuth function to get the optimised value of surface azimuth(orientaion)
    #     optimised_surface_azimuth = parameter_azimuth(row['ghi'], row['Generation [kW]'], optimised_k, surface_tilt_init, surface_azimuth_init, azimuth, zenith)

    #     #call the parameter_tilt function to get the optimised value of surface tilt
    #     optimised_surface_tilt = parameter_tilt(row['ghi'], row['Generation [kW]'], optimised_k, surface_tilt_init, optimised_surface_azimuth, azimuth, zenith)

    #     para = para.append({
    #         'k': optimised_k, 
    #         'surface_azimuth': optimised_surface_azimuth, 
    #         'surface_tilt': optimised_surface_tilt, 
    #         'sun_azimuth': azimuth, 
    #         'sun_zenith': zenith
    #         }, ignore_index=True)

    # rmse_values = pd.DataFrame(columns=['index', 'rmse_data'])   
    
    # for index , p in para.iterrows():

    #     solar_curve = pd.DataFrame(columns=['solar_data', 'actual_gen'])

    #     for _ , tcg in time_clearsky_gen.iterrows():
    #         solar_data = tcg['ghi'] * p['k'] * (math.cos(math.radians(90)-p['sun_zenith']) * math.sin(p['surface_tilt']) * math.cos(p['surface_azimuth'] - p['sun_azimuth']) + math.sin(math.radians(90)-p['sun_zenith']) * math.cos(p['surface_tilt']))
    #         if solar_data > 0:
    #             solar_curve = solar_curve.append({'solar_data':solar_data, 'actual_gen':tcg['Generation [kW]']*1000}, ignore_index= True)
        
    #     if (len(solar_curve)):
    #         rmse_data = np.sqrt(metrics.mean_squared_error(solar_curve['actual_gen'], solar_curve['solar_data']))
    #         rmse_values = rmse_values.append({'index':index, 'rmse_data':rmse_data}, ignore_index= True)
        
    
    # min_val_row = rmse_values.ix[rmse_values['rmse_data'].idxmin()]
    # final_parameters = para.ix[min_val_row['index']]
    
    # return (final_parameters['k'], final_parameters['surface_azimuth'], final_parameters['surface_tilt'])
    return 0



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