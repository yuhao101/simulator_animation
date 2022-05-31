#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
@author: zhangyuhao
@file: generate_route_info.py
@time: 2022/5/29 下午7:57
@email: yuhaozhang76@gmail.com
@desc: 
"""
import warnings
import osmnx as ox
import pickle
import math
import pandas as pd
import sys
from tqdm import tqdm
from math import radians, sin, acos, cos
warnings.filterwarnings("ignore")

env_params = {
    'north_lat': 22.51,
    'south_lat': 19.57,
    'east_lng': 113.21,
    'west_lng': 114.32
}
# G = ox.graph_from_bbox(env_params['north_lat'], env_params['south_lat'], env_params['east_lng'], env_params['west_lng'],
#                        network_type='drive')
# ox.save_graphml(G, './hongkong/hongkong.graphml')
G = ox.load_graphml('./hongkong/hongkong.graphml')
gdf_nodes, gdf_edges = ox.graph_to_gdfs(G)
lat_list = gdf_nodes['y'].tolist()
lng_list = gdf_nodes['x'].tolist()
node_id = gdf_nodes.index.tolist()
node_id_to_lat_lng = {}
node_coord_to_id = {}
for i in range(len(lat_list)):
    node_id_to_lat_lng[node_id[i]] = (lat_list[i], lng_list[i])
    node_coord_to_id[(lat_list[i], lng_list[i])] = node_id[i]

center = (
    (env_params['east_lng'] + env_params['west_lng']) / 2, (env_params['north_lat'] + env_params['south_lat']) / 2)
radius = max(abs(env_params['east_lng'] - env_params['west_lng']) / 2,
             abs(env_params['north_lat'] - env_params['south_lat']) / 2)
side = 10
interval = 2 * radius / side


def distance(coord_1, coord_2):
    """
    :param coord_1: the coordinate of one point
    :type coord_1: tuple -- (latitude,longitude)
    :param coord_2: the coordinate of another point
    :type coord_2: tuple -- (latitude,longitude)
    :return: the manhattan distance between these two points
    :rtype: float
    """
    manhattan_dis = 0
    try:
        lat1, lon1, = coord_1
        lat2, lon2 = coord_2
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        r = 6371
        if round((lon1 - lon2), 4) == 0.0000:
            lat_dis = 0
        else:
            lat_dis = r * acos(cos(lat1) ** 2 * cos(lon1 - lon2) + sin(lat1) ** 2)
        lon_dis = r * (lat2 - lat1)
        manhattan_dis = (abs(lat_dis) ** 2 + abs(lon_dis) ** 2) ** 0.5
    except Exception as e:
        print(e)
        print(coord_1)
        print(coord_2)
        print(lon1 - lon2)
        print(cos(lat1) ** 2 * cos(lon1 - lon2) + sin(lat1) ** 2)

    return manhattan_dis


def get_zone(lat, lng):
    """
    :param lat: the latitude of coordinate
    :type : float
    :param lng: the longitude of coordinate
    :type lng: float
    :return: the id of zone that the point belongs to
    :rtype: float
    """
    if lat < center[1]:
        i = math.floor(side / 2) - math.ceil((center[1] - lat) / interval) + side % 2
    else:
        i = math.floor(side / 2) + math.ceil((lat - center[1]) / interval) - 1

    if lng < center[0]:
        j = math.floor(side / 2) - math.ceil((center[0] - lng) / interval) + side % 2
    else:
        j = math.floor(side / 2) + math.ceil((lng - center[0]) / interval) - 1
    return i * side + j


# data = pd.read_csv('C:\\Users\\kejintao\\Desktop\\Transpotation_Simulator\\simulator\\input\\data.parquet')
all_data=pickle.load(open('./hongkong/hongkong_order.pickle', 'rb'))
print(all_data[list(all_data.keys())[0]][0])

ori_id_list = []
origin_lng = []
origin_lat = []
ori_grid_id_list = []

dest_id_list = []
dest_lng = []
dest_lat = []
dest_grid_id_list = []
itinerary_node_list = []
itinerary_segment_dis_list = []
dis_array = []
pickup_time = []
pickup_distance = []
ma_distance = []
for t in tqdm(all_data.keys()):
    for order in all_data[t]:
        x = ox.get_nearest_node(G, (order[2], order[3]), return_dist=False)
        point = gdf_nodes['geometry'][x]
        ori_id, temp_ori_lat, temp_ori_lng = x, point.y, point.x
        x = ox.get_nearest_node(G, (order[5], order[6]), return_dist=False)
        point = gdf_nodes['geometry'][x]
        dest_id, temp_dest_lat, temp_dest_lng = x, point.y, point.x
        if ori_id == dest_id:
            continue
        ori_id_list.append(ori_id)
        origin_lng.append(temp_ori_lng)
        origin_lat.append(temp_ori_lat)
        ori_grid_id_list.append(get_zone(temp_ori_lat,temp_ori_lng))
        dest_id_list.append(dest_id)
        dest_lat.append(temp_dest_lat)
        dest_lng.append(temp_dest_lng)
        dest_grid_id_list.append(get_zone(temp_dest_lat,temp_dest_lng))
        # pickup_distance.append(data[4])
        pickup_time.append(order[8])
        ma_distance.append(distance((temp_ori_lat,temp_ori_lng), (temp_dest_lat,temp_dest_lng)))
        ite = ox.shortest_path(G, ori_id, dest_id, weight='length', cpus=16)
        if ite is not None and len(ite) > 1:
            itinerary_node_list.append(ite)
            itinerary_segment_dis = []
            for i in range(len(ite) - 1):
                dis = distance(node_id_to_lat_lng[ite[i]],
                               node_id_to_lat_lng[ite[i + 1]])
                itinerary_segment_dis.append(dis)
            pickup_distance.append(sum(itinerary_segment_dis))
            itinerary_segment_dis_list.append(itinerary_segment_dis)
        else:
            itinerary_node_list.append([ori_id, dest_id])
            dis = distance(node_id_to_lat_lng[ori_id],
                               node_id_to_lat_lng[dest_id])
            pickup_distance.append(dis)
            itinerary_segment_dis_list.append(dis)

pd_data = pd.DataFrame()
pd_data['order_id'] = [i for i in range(len(origin_lat))]
pd_data['origin_id'] = ori_id_list
pd_data['origin_lat'] = origin_lat
pd_data['origin_lng'] = origin_lng
pd_data['dest_id'] = dest_id_list
pd_data['dest_lat'] = dest_lat
pd_data['dest_lng'] = dest_lng
pd_data['trip_distance'] = pickup_distance
pd_data['start_time'] = pickup_time
pd_data['origin_grid_id'] = ori_grid_id_list
pd_data['dest_Grid_id'] = dest_grid_id_list
pd_data['itinerary_node_list'] = itinerary_node_list
pd_data['itinerary_segment_dis_list'] = itinerary_segment_dis_list
pd_data['trip_time'] = 0
pd_data['cancel_prob'] = 0
pd_data.to_csv('./hongkong/hongkong_order.csv',index=False)
# pickle.dump(result, open('./simulator/output/multi_thread_2015.pickle', 'wb'))
