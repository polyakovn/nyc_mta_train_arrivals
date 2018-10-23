from flask import Flask, render_template, jsonify, request, make_response
import os, requests, time, csv, json
from google.transit import gtfs_realtime_pb2
from protobuf_to_dict import protobuf_to_dict
from orderedset import OrderedSet

class MTA():

    def __init__(self):
        self.stations = []
        self.station_names = []

    def make_station_list(self):
        with open('static/Stations.csv') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                station_name = row[5]
                station_lines = row[7].split(" ")
                station_id = row[2]
                self.add_or_modify_station(station_name, station_lines, station_id) #some station names have multiple ids/lines

    def add_or_modify_station(self, station_name, station_lines, station_id):
        for station in self.stations:
            if station.name == station_name: #if a station with this name already exists, modify it
                station.add_lines(station_lines)
                station.add_id(station_id)
                return
        station = Station(station_name, station_lines, station_id)
        self.stations.append(station)

    def make_station_names(self):
        f = open("static/stop_names.txt")
        content = f.readlines()
        self.station_names = [line.strip() for line in content]

    def get_station(self, name):
        for station in self.stations:
            if name == station.name:
                return station

    def get_station_arrivals(self, station_name):
        api_key = '75b4f38677044eca8103ef4bea7cd386'
        all_arrivals = []
        station = self.get_station(station_name)
        train_feeds = station.get_train_feeds()
        for train_feed in train_feeds:
            feed = gtfs_realtime_pb2.FeedMessage()
            response = requests.get('http://datamine.mta.info/mta_esi.php?key=' + api_key + '&feed_id=' + str(train_feed))
            feed.ParseFromString(response.content)
            subway_feed = protobuf_to_dict(feed)
            realtime_data = subway_feed['entity']
            self.get_next_arrivals(realtime_data, station)
        return station.next_arrivals


    def get_next_arrivals(self, train_feed, station):
        id_options = self.get_id_possibilities(station)
        for train in train_feed:
            if train.get('trip_update', False) != False:
                train_arrivals = train['trip_update']['stop_time_update']
                train_line = train['trip_update']['trip']['route_id']
                for arrival in train_arrivals:
                    stop_id = arrival['stop_id']
                    arrival_time = arrival['arrival']['time']
                    if stop_id in id_options and arrival_time != None:
                        arrival_time = self.get_minutes_from_now(arrival_time)
                        if arrival_time > 0:
                            self.add_or_modify_arrival(station, train_line, stop_id, arrival_time)

    def add_or_modify_arrival(self, station, train_line, stop_id, arrival_time):
        for arrival in station.next_arrivals:
            if arrival.line == train_line and arrival.direction == stop_id[-1]:
                arrival.arrival_times.append(arrival_time)
                return
        arrival = Arrival(train_line, stop_id, arrival_time)
        station.add_arrival(arrival)

    def get_minutes_from_now(self, epoch_time):
        current_time = int(time.time())
        time_until_train = int(int(epoch_time - current_time) / 60)
        return time_until_train

    def get_id_possibilities(self, station):
        id_list = []
        for station_id in station.ids:
            id_list.append(station_id + "S")
            id_list.append(station_id + "N")
        return id_list

class Station():

    def __init__(self, name, lines, station_id):
        self.name = name
        self.lines = lines
        self.ids = [station_id]
        self.next_arrivals = []

    def add_lines(self, new_lines):
        self.lines.extend(new_lines)

    def add_id(self, station_id):
        self.ids.append(station_id)

    def add_arrival(self, arrival):
        self.next_arrivals.append(arrival)

    def get_train_feeds(self):
        station_lines = set(self.lines)
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


class Arrival():

    def __init__(self, line, stop_id, arrival_time):
        self.line = line
        self.direction = stop_id[-1]
        self.arrival_times = [arrival_time]

app = Flask(__name__)
mta = MTA()
mta.make_station_list()
mta.make_station_names()
stop_names = mta.station_names

@app.route('/')
def setup_page():
    return render_template("home.html", stop_names = stop_names)

@app.route('/station_info')
def get_station_info():
    station_name = request.args['station']
    arrivals_list = mta.get_station_arrivals(station_name)
    return turn_to_json(arrivals_list)

@app.route('/filter_by_line')
def add_line_filter():
    station_name = request.args['station']
    line_filter = request.args['line']
    arrivals_list = mta.get_station_arrivals(station_name)
    filtered_arrivals = []
    for arrival in arrivals_list:
        if arrival.line == line_filter:
            filtered_arrivals.append(arrival)
    return turn_to_json(filtered_arrivals)

@app.route('/filter_by_direction')
def add_direction_filter():
    station_name = request.args['station']
    direction_filter = request.args['direction']
    arrivals_list = mta.get_station_arrivals(station_name)
    filtered_arrivals = []
    for arrival in arrivals_list:
        if arrival.direction == direction_filter:
            filtered_arrivals.append(arrival)
    return turn_to_json(filtered_arrivals)

@app.route('/filter_by_line_and_direction')
def add_line_and_direction_filter():
    station_name = request.args['station']
    direction_filter = request.args['direction']
    line_filter = request.args['line']
    arrivals_list = mta.get_station_arrivals(station_name)
    filtered_arrivals = []
    for arrival in arrivals_list:
        if arrival.direction == direction_filter and arrival.line == line_filter:
            filtered_arrivals.append(arrival)
    return turn_to_json(filtered_arrivals)

def turn_to_json(arrivals_list):
    arrival_string = '['
    for arrival in arrivals_list:
        arrival_times_string = '['
        for time in arrival.arrival_times:
            arrival_times_string += '"' + str(time) + '",'
        arrival_times_string = arrival_times_string[:-1]
        arrival_times_string += ']'
        arrival_string += '{"line":"' + arrival.line + '", "direction":"' + arrival.direction + '", "arrival_times":' + arrival_times_string + "},"
    arrival_string = arrival_string[:-1]
    arrival_string += "]"
    return arrival_string
