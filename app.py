from flask import Flask, render_template, jsonify, request
import os, requests, time, csv, json
from google.transit import gtfs_realtime_pb2
from protobuf_to_dict import protobuf_to_dict
from orderedset import OrderedSet

app = Flask(__name__)
stop_dict = {}
stop_names = []
api_key = '75b4f38677044eca8103ef4bea7cd386'

with open('Stations.csv') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    for row in csv_reader:
        station_id = row[2]
        station_name = row[5]
        station_lines = row[7]
        stop_names.append(station_name)
        stop_dict[station_id] = (station_name, station_lines)
stop_names = OrderedSet(sorted(stop_names))

def name_to_ids(station_name):
    key_list = []
    for key in stop_dict:
        if stop_dict[key][0] == station_name:
            key_list.append(key)
    return key_list

def find_train_feeds(station_id):
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

def convert_time(epoch_time):
    return (time.strftime("%H:%M %Z",time.localtime(epoch_time)))

def time_from_now(epoch_time):
    current_time = int(time.time())
    time_until_train = int(int(epoch_time - current_time) / 60)
    return time_until_train

class Train:
    def __init__(self, station, line, times):
        self.station = station
        self.line = line
        self.times = times
        self.direction = station[-1]


def find_next_arrivals(train_feed, station_id):
    south_id = station_id + "S"
    north_id = station_id + "N"
    train_dict = {}
    for train in train_feed:
        if train.get('trip_update', False) != False:
            train_schedule = train['trip_update']
            stop_times = train['trip_update']['stop_time_update']
            line = train_schedule['trip']['route_id']
            for arrivals in stop_times:
                stop_id = arrivals['stop_id']
                if south_id == stop_id or north_id == stop_id:
                    arrival_time = arrivals['arrival']['time']
                    if arrival_time != None:
                        time_diff = time_from_now(arrival_time)
                        if time_diff >= 0:
                            stop_line = stop_id + " " + line
                            if stop_line not in train_dict:
                                train_dict[stop_line] = [time_diff]
                            else:
                                train_dict[stop_line].append(time_diff)
    return train_dict

@app.route('/')
def main_page():
    return "hi"

@app.route('/stops')
def stops():
    return render_template("home.html", stop_names = stop_names)

@app.route('/station_info')
def get_station_info(station_name=None):
    if not station_name:
        station_name = request.args['station']
        return_all = True
    else:
        return_all = False
    station_ids = name_to_ids(station_name)
    all_arrivals = {}
    for station_id in station_ids:
        train_feeds = find_train_feeds(station_id) #works
        for train_feed in train_feeds:
            feed = gtfs_realtime_pb2.FeedMessage()
            response = requests.get('http://datamine.mta.info/mta_esi.php?key=' + api_key + '&feed_id=' + str(train_feed))
            feed.ParseFromString(response.content)
            subway_feed = protobuf_to_dict(feed)
            realtime_data = subway_feed['entity']
            next_arrivals = find_next_arrivals(realtime_data, station_id) #returns train dict
            all_arrivals = {**all_arrivals, **next_arrivals}
    if return_all:
        return jsonify(all_arrivals)
    else:
        return all_arrivals

@app.route('/line_station_info')
def get_line_info():
    station_name = request.args['station']
    line_name = request.args['line']
    train_dict = get_station_info(station_name)
    for train in train_dict.copy():
        line = train.split(" ")[1]
        if line != line_name:
            del train_dict[train]
    return jsonify(train_dict)
