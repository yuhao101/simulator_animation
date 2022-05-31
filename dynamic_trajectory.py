import folium
import os
from tqdm import tqdm
from folium import plugins
import pickle
import json
import csv
import sys


def draw_gps(locations_true, output_path, file_name):
    """
    绘制gps轨迹图
    :param locations: list, 需要绘制轨迹的经纬度信息，格式为[[lat1, lon1], [lat2, lon2], ...]
    :param output_path: str, 轨迹图保存路径
    :param file_name: str, 轨迹图保存文件名
    :return: None
    """
    m = folium.Map(locations_true[0][0], zoom_start=30, attr='default')  # 中心区域的确定
    for single_route in locations_true:

        lc = folium.PolyLine(  # polyline方法为将坐标用实线形式连接起来
            single_route,  # 将坐标点连接起来
            weight=4,  # 线的大小为4
            color='red',  # 线的颜色为红色
            opacity=0.8,  # 线的透明度
        ).add_to(m)  # 将这条线添加到刚才的区域m内

        # attr = {"fill": "#007DEF", "font-weight": "bold", "font-size": "20"}
        # plugins.PolyLineTextPath(
        #     lc, "--> **", repeat=True, offset=5, attributes=attr
        # ).add_to(m)
        plugins.AntPath(
            locations=single_route, reverse=False, dash_array=[20, 30]
        ).add_to(m)

        folium.Marker(single_route[0], popup='<b>Starting Point</b>').add_to(m)
        folium.Marker(single_route[-1], popup='<b>End Point</b>').add_to(m)

    m.save(os.path.join(output_path, file_name))  # 将结果以HTML形式保存到指定路径


def generate_route_lat_lng(route_file, node_file):
    route_info = pickle.load(open(route_file, 'rb'))
    with open('./data/node_json.json', 'r', encoding='utf-8') as file:
        id_lng_lat = json.load(file)
    route = []
    for i in range(len(route_info)):
        temp_route = []
        for node in route_info.iloc[i]['itinerary_segment_dis_list']:
            if str(node) in list(id_lng_lat.keys()):
                temp_route.append(id_lng_lat[str(node)])
            else:
                print(node)
        route.append(temp_route)
    return route


def generate_car_csv(all_route):
    route_file = open('./data/route.csv', 'w')
    route_csv = csv.writer(route_file)
    route_csv.writerow(['geometry'])
    for s_route in all_route:
        temp_lat_lng = []
        for item in s_route:
            temp_lat_lng.append([item[1],item[0]])
        temp_route = {
            "type": "LineString",
            "coordinates": temp_lat_lng
        }
        route_csv.writerow([json.dumps(temp_route)])


def generate_route_time(record_path):
    records = pickle.load(open(record_path, 'rb'))
    routes = {}
    routes['data'] = []
    driver_cruising = {}
    length = 0
    for record in tqdm(records):
        length += 1
        if length == 100:
            break
        for key in record:
            driver = record[key]
            if isinstance(driver[0], list):
                if key in driver_cruising.keys():
                    temp_time = driver_cruising[key][0]
                    temp_time.append(driver[0][-1])
                    temp_coordinate = driver_cruising[key][1]
                    temp_coordinate.append([driver[0][0], driver[0][1]])
                    temp_type = 0.0
                    routes['data'].append({
                        'time_list': temp_time,
                        'traj_list': temp_coordinate,
                        'type': temp_type
                    })
                    driver_cruising[key] = [[], []]
                temp_time = []
                temp_coordinate = []
                temp_type = 2.0
                flag = True
                for position in driver:
                    temp_time.append(position[-1])
                    temp_coordinate.append([position[0], position[1]])
                    if position[-2] == 1.0 and flag:
                        routes['data'].append({
                            'time_list': temp_time,
                            'traj_list': temp_coordinate,
                            'type': temp_type
                        })
                        temp_type = 1.0
                        temp_coordinate = [[position[0], position[1]]]
                        temp_time = [position[-1]]
                        flag = False
                routes['data'].append({
                    'time_list': temp_time,
                    'traj_list': temp_coordinate,
                    'type': temp_type
                })
            else:
                if key not in driver_cruising.keys():
                    driver_cruising[key] = [[driver[-1]], [[driver[0], driver[1]]]]
                else:
                    driver_cruising[key][0].append(driver[-1])
                    driver_cruising[key][1].append([driver[0], driver[1]])
    file = open('./data/simulator_animation_100.json', 'w')
    file.write(json.dumps(routes, indent=1))


def calculate_metrics(record_path):
    records = pickle.load(open(record_path, 'rb'))
    order = pickle.load(open('./data/order.pickle', 'rb'))
    order_num_time = {}
    matched_rate_time = {}
    current_num = 0
    matched_num = 0
    driver_no_cruising_time = {}
    for i in range(36000, 79200, 5):
        for j in range(0, 5):
            if (i+j) in order.keys():
                current_num += len(order[i+j])
        order_num_time[i] = current_num
    for i, time in enumerate(tqdm(records)):
        for driver in time:
            if driver not in driver_no_cruising_time.keys():
                driver_no_cruising_time[driver] = [set(), set()]
            if isinstance(time[driver][0], list):
                record = time[driver]
                matched_num += 1
                for single_record in record:
                    if single_record[-2] == 1.0:
                        for second in range(i*5+36000, int(single_record[-1])):
                            driver_no_cruising_time[driver][0].add(second)
                        for second in range(int(single_record[-1]), int(record[-1][-1])):
                            driver_no_cruising_time[driver][1].add(second)
                        break
        matched_rate_time[i*5+36000] = [matched_num/order_num_time[i*5+36000]]
    for key in tqdm(matched_rate_time.keys()):
        pickup_count = 0
        delivery_count = 0
        cruising_count = 0
        for driver in driver_no_cruising_time.keys():
            if key in driver_no_cruising_time[driver][0]:
                pickup_count += 1
            elif key in driver_no_cruising_time[driver][1]:
                delivery_count += 1
            else:
                cruising_count += 1
        matched_rate_time[key].append(pickup_count/2000)
        matched_rate_time[key].append(delivery_count/2000)
        matched_rate_time[key].append(cruising_count/2000)
    file = open('./data/simulator_metrics.json', 'w')
    file.write(json.dumps(matched_rate_time, indent=1))


def generate_driver_heatmap():
    heatMap = []
    driver = pickle.load(open('./data/driver_info.pickle', 'rb')).head(2000)
    for i in range(2000):
        driver_coordinate = driver.loc[i, ['lng','lat']]
        heatMap.append([driver_coordinate['lng'],driver_coordinate['lat']])
    file = open('./data/headMap.json', 'w')
    file.write(json.dumps(heatMap, indent=1))


def generate_order_heatmap():
    heatMap = []
    order_info = pickle.load(open('./data/order.pickle', 'rb'))
    for i in range(36000, 79200):
        if i in order_info.keys():
            for order in order_info[i]:
                heatMap.append([order[3], order[2]])
    file = open('./data/order_headMap.json', 'w')
    file.write(json.dumps(heatMap, indent=1))


def generate_driver_info_by_records(record_path):
    heatMap = []
    driver_coordinate = {}
    records = pickle.load(open(record_path, 'rb'))
    for record in tqdm(records):
        for driver in record.keys():
            if isinstance(record[driver][0], list):
                driver_coordinate[driver] = [record[driver][-1][1], record[driver][-1][0]]
            else:
                driver_coordinate[driver] = [record[driver][1], record[driver][0]]
    for value in driver_coordinate.values():
        heatMap.append(value)
    file = open('./data/driver_after_delivery_headMap.json', 'w')
    file.write(json.dumps(heatMap, indent=1))


def generate_order_info_by_records(record_path):
    heatMap = []
    order_origin_info = {}
    order_info = pickle.load(open('./data/order.pickle', 'rb'))
    for i in tqdm(range(36000, 79200)):
        if i in order_info.keys():
            for order in order_info[i]:
                order_origin_info[order[0]] = [order[3], order[2]]
    records = pickle.load(open(record_path, 'rb'))
    finished_order = set()
    for record in tqdm(records):
        for driver in record.keys():
            if isinstance(record[driver][0], list):
                finished_order.add(record[driver][0][2])

    for key in order_origin_info.keys():
        if key in finished_order:
            continue
        heatMap.append(order_origin_info[key])
    print(len(heatMap))
    print(len(order_origin_info))
    file = open('./data/order_after_delivery_cruising_headMap.json', 'w')
    file.write(json.dumps(heatMap, indent=1))


def extract_driver_record(record_path):
    records = pickle.load(open(record_path, 'rb'))
    driver_num = 5
    driver_records = {}
    driver_temp = {}
    for id in range(driver_num):
        driver_records[str(id)] = []
        driver_temp[str(id)] = []
    for record in tqdm(records):
        for driver in record:
            if isinstance(record[driver][0], list):
                if driver in driver_records.keys():
                    driver_records[driver].append({
                        "geometry": {
                            "type": "LineString",
                            "coordinates": driver_temp[driver]
                        },
                        "color": 'yellow'
                    })
                    single_record = record[driver]
                    temp_coordinates = []
                    for coor in single_record:
                        temp_coordinates.append([coor[0], coor[1]])
                        if coor[-2] == 1.0:
                            driver_records[driver].append({
                                "geometry": {
                                    "type": "LineString",
                                    "coordinates": temp_coordinates
                                },
                                "color": 'green'
                            })
                            temp_coordinates = [[coor[0], coor[1]]]
                    driver_records[driver].append({
                        "geometry": {
                            "type": "LineString",
                            "coordinates": temp_coordinates
                        },
                        "color": 'red'
                    })
                    driver_temp[driver] = []
            else:
                if driver in driver_temp.keys():
                    driver_temp[driver].append([record[driver][0], record[driver][1]])
    print(driver_records)
    file = open('./data/animation_car_line_test.json', 'w')
    file.write(json.dumps(driver_records['0'], indent=1))


def extract_one_driver_record(record_path):
    records = pickle.load(open(record_path, 'rb'))
    driver_records = {
        '5': {
            'geometry': {
                'type': 'LineString',
                'coordinates': []
            }
        }
    }
    for record in tqdm(records):
        for driver in record:
            if isinstance(record[driver][0], list):
                if driver in driver_records.keys():
                    for coor in record[driver]:
                        driver_records[driver]['geometry']['coordinates'].append([coor[0], coor[1]])
            else:
                if driver in driver_records.keys():
                    driver_records[driver]['geometry']['coordinates'].append([record[driver][0], record[driver][1]])
    print(driver_records)
    file = open('./data/animation_car_line.json', 'w')
    file.write(json.dumps(driver_records, indent=1))


def calculate_metrics_passenger(record_path):
    records = pickle.load(open(record_path, 'rb'))
    order = pickle.load(open('./data/order.pickle', 'rb'))
    order_to_time = {}
    prematching_time = {}
    for i in range(36000, 79200, 5):
        for j in range(0, 5):
            if (i + j) in order.keys():
                for single_order in order[i+j]:
                    order_to_time[single_order[0]] = i

    prematching_time_temp_list = []
    postmatching_time_temp_list = []
    for i, time in enumerate(tqdm(records)):
        temp_pre = []
        temp_post = []
        if prematching_time_temp_list == []:
            prematching_time[i*5+36000] = [0, 0]
        else:
            if len(prematching_time_temp_list) < 361:
                if (sum(len(i) for i in prematching_time_temp_list)) == 0:
                    prematching_time[i * 5 + 36000] = [0]
                else:
                    prematching_time[i*5+36000] = [sum(sum(i) for i in prematching_time_temp_list)/(sum(len(i) for i in prematching_time_temp_list))]
                if (sum(len(i) for i in postmatching_time_temp_list)) == 0:
                    prematching_time[i * 5 + 36000].append(0)
                else:
                    prematching_time[i*5+36000].append(sum(sum(i) for i in postmatching_time_temp_list)/(sum(len(i) for i in postmatching_time_temp_list)))
            else:
                prematching_time[i * 5 + 36000] = [
                    sum(sum(i) for i in prematching_time_temp_list[1:]) / (sum(len(i) for i in prematching_time_temp_list[1:]))]
                prematching_time[i * 5 + 36000].append(sum(sum(i) for i in postmatching_time_temp_list[1:]) / (
                    sum(len(i) for i in postmatching_time_temp_list[1:])))
                prematching_time_temp_list = prematching_time_temp_list[1:]
                postmatching_time_temp_list = postmatching_time_temp_list[1:]
        for driver in time:
            if isinstance(time[driver][0], list):
                record = time[driver]
                matching_time = record[0][-1]
                pickup_end_time = 79200
                for single_record in record:
                    if single_record[-2] == 1:
                        pickup_end_time = min(single_record[-1], pickup_end_time)
                        break
                temp_pre.append(matching_time - order_to_time[record[0][2]])
                temp_post.append(pickup_end_time - matching_time)
        prematching_time_temp_list.append(temp_pre)
        postmatching_time_temp_list.append(temp_post)

    file = open('./data/simulator_metrics_passenger.json', 'w')
    file.write(json.dumps(prematching_time, indent=1))


if __name__ == '__main__':
    record_path = './data/record/'
    record_file = os.listdir(record_path)
    print(record_file)
    for file in record_file[2:3]:
        generate_route_time(record_path+file)
        # calculate_metrics(record_path+file)
        # extract_one_driver_record(record_path+file)
        # calculate_metrics_passenger(record_path+file)

    # generate_driver_heatmap()
    # generate_order_heatmap()
    # record_path = './data/record/records_driver_num_2000_cruising.pickle'
    # generate_order_info_by_records(record_path)