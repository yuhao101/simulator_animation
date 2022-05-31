#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
@author: zhangyuhao
@file: handle_hongkong_data.py
@time: 2022/5/23 下午4:18
@email: yuhaozhang76@gmail.com
@desc: 
"""
import pandas as pd
import time
import datetime
import pickle
from tqdm import tqdm


def handle_hongkong_data():
    max_lng = float('-inf')
    min_lng = float('inf')
    max_lat = float('-inf')
    min_lat = float('inf')
    ## generate one day data
    # selected_date = '2009/6/28 0:00:00'
    # file = pd.read_csv('./hongkong/TAXIWEEK2.csv', header=None)
    # file.columns = ['PosID', 'DevID', 'HkDt', 'HkTm', 'LAT', 'LON', 'SpeedKmHr',
    #                 'Direction', 'ACC', 'FlagDown', 'Satellite']
    # data = file[file['HkDt'] == selected_date]
    # print(data.head(5))
    # print(data.shape)
    # data.to_csv('./hongkong/hongkong_6_28.csv', header=True, index=False)

    ## handle data
    data = pd.read_csv('./hongkong/hongkong_6_28.csv')
    print(data.head(5))
    driver = list(dict(data['DevID'].value_counts()).keys())
    print(driver)
    order_id = 0
    order = {}
    for single_driver in tqdm(driver):
        carried = False
        temp_data = data[data['DevID'] == single_driver]
        for i in range(len(temp_data)):
            record = temp_data.iloc[i]
            flag = record['FlagDown']
            if carried and flag == 1:
                continue
            elif flag == 1:
                carried = True
                origin_lat = record['LAT']
                origin_lng = record['LON']
                temp_time = time.strptime(record['HkTm'].split(' ')[1], '%H:%M:%S')
                start_time = int(datetime.timedelta(hours=temp_time.tm_hour, minutes=temp_time.tm_min, seconds=
                                                    temp_time.tm_sec).total_seconds())
            elif carried:
                dest_lat = record['LAT']
                dest_lng = record['LON']
                if origin_lat > 30 or origin_lat <= 10 or origin_lng > 120 or origin_lng <= 100 or dest_lat > 30 or dest_lat \
                        <= 10 or dest_lng > 120 or dest_lng <= 100:
                    continue
                max_lat = max(max_lat, origin_lat)
                max_lat = max(max_lat, dest_lat)
                min_lat = min(min_lat, origin_lat)
                min_lat = min(min_lat, dest_lat)
                max_lng = max(max_lng, origin_lng)
                max_lng = max(max_lng, dest_lng)
                min_lng = min(min_lng, origin_lng)
                min_lng = min(min_lng, dest_lng)
                order_info = [order_id, 0, origin_lat, origin_lng, 0, dest_lat, dest_lng, 0, start_time, 0, 0, [], [],
                              0, 0, 0]
                order_id += 1
                if start_time not in order.keys():
                    order[start_time] = [order_info]
                else:
                    order[start_time].append(order_info)
                carried = False
    print(len(order.keys()))
    print(max_lat)
    print(min_lat)
    print(max_lng)
    print(min_lng)
    pickle.dump(order, open('./hongkong/hongkong_order.pickle', 'wb'))


if __name__ == '__main__':
    handle_hongkong_data()