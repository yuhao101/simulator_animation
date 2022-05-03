#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
@author: zhangyuhao
@file: brige_info.py
@time: 2022/4/21 下午11:18
@email: yuhaozhang76@gmail.com
@desc: 
"""
import osmnx as ox
import pickle
import sys
import pandas as pd
import datetime
from tqdm import tqdm
import warnings
warnings.filterwarnings("ignore")


def generate_bridge_info():
    G = ox.load_graphml('./data/graph.graphml')
    gdf_nodes, gdf_edges = ox.graph_to_gdfs(G)
    lat_list = gdf_nodes['y'].tolist()
    lng_list = gdf_nodes['x'].tolist()
    node_id = gdf_nodes.index.tolist()
    node_id_to_lat_lng = {}
    node_coord_to_id = {}
    for i in range(len(lat_list)):
        node_id_to_lat_lng[node_id[i]] = (lat_list[i], lng_list[i])
        node_coord_to_id[(lat_list[i], lng_list[i])] = node_id[i]

    bridges_coordinate = {'Manhattan': [(-73.992, 40.71027), (-73.9886, 40.7037)],
                          'Brooklyn': [(-73.9946, 40.7044), (73.9995, 40.7082)]}
    bridges_node_list = {}
    for bridge in bridges_coordinate:
        bridge_start = ox.distance.get_nearest_node(G, (bridges_coordinate[bridge][0][1], bridges_coordinate[bridge][0][0]), method=None, return_dist=False)
        bridge_end = ox.distance.get_nearest_node(G, (bridges_coordinate[bridge][1][1], bridges_coordinate[bridge][1][0]), method=None, return_dist=False)
        bridge_node_list = set(ox.distance.shortest_path(G, bridge_start, bridge_end, weight='length', cpus=16))
        bridges_node_list[bridge] = bridge_node_list
    orders = pickle.load(open('./data/order.pickle', 'rb'))
    time_interval = 300
    columns = ['time']
    for bridge in bridges_node_list.keys():
        columns.append(bridge+'_bridge_flow')
    flow_data = pd.DataFrame(columns=columns)
    for i in tqdm(range(time_interval, 86401, time_interval)):
        flow_info = {
            'time': str(datetime.timedelta(seconds=i))
        }
        for bridge in bridges_node_list:
            flow = 0
            for j in range(i-300, i):
                if j in orders.keys():
                    for order in orders[j]:
                        for node in order[11]:
                            if node in bridges_node_list[bridge]:
                                flow += 1
                                break
            flow_info[bridge+'_bridge_flow'] = flow

        flow_data = flow_data.append(flow_info, ignore_index=True)

    flow_data.to_csv('./data/Bridge_flow.csv', index=False)


if __name__ == '__main__':
    generate_bridge_info()



