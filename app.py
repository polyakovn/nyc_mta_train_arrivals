from flask import Flask, render_template, jsonify, request, make_response
import os, requests, time, csv, json
from google.transit import gtfs_realtime_pb2
from protobuf_to_dict import protobuf_to_dict
from orderedset import OrderedSet

app = Flask(__name__)
stop_dict = {}
stop_names = []
api_key = '75b4f38677044eca8103ef4bea7cd386'

def initialize_stop_names_and_stop_dict():
    global stop_names, stop_dict
    with open('static/Stations.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            station_id = row[2]
            station_name = row[5]
            station_lines = row[7]
            stop_names.append(station_name)
            stop_dict[station_id] = (station_name, station_lines)
    stop_names = OrderedSet(sorted(stop_names))

initialize_stop_names_and_stop_dict()

def get_next_arrivals(train_feed, station_id):
    train_dict = {}
    south_id = station_id + "S"
    north_id = station_id + "N"
    for train in train_feed:
        if train.get('trip_update', False) != False:
            train_arrivals = train['trip_update']['stop_time_update']
            train_line = train['trip_update']['trip']['route_id']
            for arrival in train_arrivals:
                stop_id = arrival['stop_id']
                if stop_id == south_id or stop_id == north_id:
                    add_arrival_to_train_dict(arrival, train_line, stop_id, train_dict)
    print(train_dict)
    return train_dict

def add_arrival_to_train_dict(arrival, train_line, stop_id, train_dict):
    arrival_time = arrival['arrival']['time']
    if arrival_time != None:
        time_from_now = get_minutes_from_now(arrival_time)
        if time_from_now > 0:
            stop_line = stop_id + " " + train_line
            if stop_line not in train_dict:
                train_dict[stop_line] = [time_from_now]
            else:
                train_dict[stop_line].append(time_from_now)

def get_minutes_from_now(epoch_time):
    current_time = int(time.time())
    time_until_train = int(int(epoch_time - current_time) / 60)
    return time_until_train

@app.route('/')
def setup_page():
    return render_template("home.html", stop_names = stop_names)

@app.route('/line_station_info')
def filter_results_by_line():
    station_name = request.args['station']
    line_name = request.args['line']
    train_dict = get_station_info(station_name)
    for train in train_dict.copy():
        line = train.split(" ")[1]
        if line != line_name:
            del train_dict[train]
    return jsonify(train_dict)

@app.route('/station_info')
def get_station_info(station_name=None):
    if not station_name:
        station_name = request.args['station']
        return_all = True
    else:
        return_all = False
    station_ids = get_station_ids(station_name)
    all_arrivals = {}
    for station_id in station_ids:
        train_feeds = get_train_feeds(station_id)
        for train_feed in train_feeds:
            feed = gtfs_realtime_pb2.FeedMessage()
            response = requests.get('http://datamine.mta.info/mta_esi.php?key=' + api_key + '&feed_id=' + str(train_feed))
            feed.ParseFromString(response.content)
            subway_feed = protobuf_to_dict(feed)
            realtime_data = subway_feed['entity']
            next_arrivals = get_next_arrivals(realtime_data, station_id) #returns train dict
            all_arrivals = {**all_arrivals, **next_arrivals}
    if return_all:
        return jsonify(all_arrivals)
    else:
        return all_arrivals

def get_station_ids(station_name):
    key_list = []
    for key in stop_dict:
        if stop_dict[key][0] == station_name:
            key_list.append(key)
    return key_list

def get_train_feeds(station_id):
    station_lines = set(stop_dict[station_id][1])
    train_feeds = []
    if station_lines.intersection(set(['1','2','3','4','5','6','S'])):
        train_feeds.append(1)
    if station_lines.intersection(set(['A','C','E','H','S'])):
        train_feeds.append(26)
    if station_lines.intersection(set(['N','Q','R','W'])):
        train_feeds.append(16)
    if station_lines.intersection(set(['B','D','F','M'])):
        train_feeds.append(21)
    if station_lines.intersection(set(['L'])):
        train_feeds.append(2)
    if station_lines.intersection(set(['SIR'])):
        train_feeds.append(11)
    if station_lines.intersection(set(['G'])):
        train_feeds.append(31)
    if station_lines.intersection(set(['J','Z'])):
        train_feeds.append(36)
    if station_lines.intersection(set(['7'])):
        train_feeds.append(51)
    return train_feeds
