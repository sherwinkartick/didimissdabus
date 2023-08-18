import concurrent
import json
import threading
import time
from typing import List

from flask import Flask, request
from flask_cors import CORS

import mathy_module as mathy
import models_module as mm
import request_and_parsing_module as rpm
import statesman_module as blob

app = Flask(__name__)
CORS(app)

all_route_tags: list[mm.Route] = []


def output_direction_locations_json():
    route = "501"
    stop_tag = "3399"
    directions, stops = get_route_details(route)
    stop = get_stop_from_directions(stop_tag, stops)
    print(f'{stop.title}')

    last_update_time = '0'
    delay = 20

    for i in range(100):
        xml = rpm.request_vehicle_locations(route, last_update_time)
        last_update_time, vehicle_location_snapshots = rpm.extract_vehicle_location_snapshots(xml)

        for vls in vehicle_location_snapshots:
            relative_position_to_stop = mathy.relative_position_to_stop(stop, directions, vls)
            # print(f'{vls.vehicle_id} {vls.dir_tag} {relative_position_to_stop}')
            state = None
            match relative_position_to_stop:
                case "before_stop_of_interest":
                    state = "before"
                case "after_stop_of_interest":
                    state = "after"
                case "vrd_unknown_stop_of_interest_may_be_on_vrd":
                    state = "unknown"
                case _:
                    continue

            report_time = int(vls.last_time / 1000) - vls.secs_since_report

            row = {}
            row['id'] = vls.vehicle_id
            row['time'] = report_time
            row['lat'] = vls.lat
            row['lng'] = vls.lon
            row['state'] = state
            row['dirTag'] = vls.dir_tag
            print(json.dumps(row))
        time.sleep(delay)


def blob_update_vlss(route_tag: str, last_update_time: str):
    last_update_time, vehicle_location_snapshots = get_latest_vehicle_locations(last_update_time, route_tag)
    blob.blob.add_vls(vehicle_location_snapshots)
    return last_update_time

def vehicleLocations_update_loop(route_tags : List[str]):
    last_update_times = {}
    delay = 15
    for route_tag in route_tags:
        last_update_times[route_tag] = '0'
    while 1:
        start_time = int(time.time())
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = []
            completed_futures: int = 0
            for route_tag in route_tags:
                futures.append(executor.submit(blob_update_vlss, route_tag=route_tag,
                                               last_update_time=last_update_times[route_tag]))
            for future in concurrent.futures.as_completed(futures):
                completed_futures += 1
                # print(f'compeleted {completed_futures}')
                last_update_time = future.result()
                last_update_times[route.tag] = last_update_time
        end_time = int(time.time())
        total_time = end_time - start_time
        # print(f'{total_time}')
        time.sleep(delay - total_time)


def routeConfig_update_loop(routes):
    last_update_times = {}
    delay = 30
    for route in routes:
        last_update_times[route] = '0'
    while 1:
        for route in routes:
            last_update_time, vehicle_location_snapshots = get_latest_vehicle_locations(last_update_times[route], route)
            # print(f'{route} {len(vehicle_location_snapshots)}')
            last_update_times[route] = last_update_time
            blob.blob.add_vls(vehicle_location_snapshots)
        time.sleep(delay)


def get_route_list():
    xml = rpm.request_route_list()
    routes = rpm.extract_route_list(xml)
    return routes


def get_latest_vehicle_locations(last_update_time: str, route_tag: str):
    xml = rpm.request_vehicle_locations(route_tag, last_update_time)
    last_update_time, vehicle_location_snapshots = rpm.extract_vehicle_location_snapshots(xml)
    return last_update_time, vehicle_location_snapshots


def get_stop_from_directions(stop_tag, stops):
    stop = next(stop for stop in stops if stop.tag == stop_tag)
    return stop


def get_route_details(route: str):
    xml = rpm.request_route_config(route)
    route_obj = rpm.extract_route_config(xml)
    return route_obj


def vls_to_api_dict(vls: mm.VehicleLocationSnapshot):
    report_time = int(vls.last_time / 1000) - vls.secsSinceReport
    row = {}
    row['id'] = vls.id
    row['time'] = report_time
    row['lat'] = vls.lat
    row['lng'] = vls.lon
    row['dirTag'] = vls.dirTag
    row['dirName'] = blob.blob.get_direction_by_tag(vls.dirTag).name
    row['routeTag'] = vls.routeTag
    row['heading'] = vls.heading
    row['speed'] = vls.speedKmHr
    return row


def print_locations(route):
    vlss = blob.blob.get_latest(route)
    for vls in vlss:
        row = vls_to_api_dict(vls)
        print(json.dumps(row))


@app.route('/locations/<route>', methods=['GET'])
def locations(route):
    vlss = blob.blob.get_latest(route)
    locations_array = []
    for vls in vlss:
        row = vls_to_api_dict(vls)
        locations_array.append(row)  # print(json.dumps(row))
    retval = json.dumps(locations_array)
    return retval


@app.route('/routes/locations', methods=['POST'])
def routes_locations():
    routes = request.get_json()
    locations_array = []
    for route in routes:
        vlss = blob.blob.get_latest(route)
        for vls in vlss:
            row = vls_to_api_dict(vls)
            locations_array.append(row)  # print(json.dumps(row))
    retval = json.dumps(locations_array)
    return retval


def stop_to_api_dict(stop: mm.Stop, route: mm.Route):
    row = {}
    row['tag'] = stop.tag
    row['title'] = stop.title
    row['lat'] = stop.lat
    row['lng'] = stop.lon
    row['stopId'] = stop.stopId
    row['dirName'] = get_dir_name(stop)
    row['routeTag'] = route.tag
    return row


def get_dir_name(stop: mm.Stop):
    retval = stop.directions[0].name
    for direction in stop.directions:
        if retval != direction.name:
            print(f'Weird issue with stop {stop.stopId}')
    return stop.directions[0].name


def get_route_tag(stop: mm.Stop):
    retval = stop.routes[0].tag
    for direction in stop.directions:
        if retval != direction.name:
            print(f'Weird issue with stop {stop.stopId}')
    return stop.directions[0].name


def print_stops(route_tags: List[str]):
    for route_tag in route_tags:
        route = blob.blob.get_route_by_tag(route_tag)
        for stop in route.stops:
            row = stop_to_api_dict(stop, route)
            print(json.dumps(row))


@app.route('/stops/<route>', methods=['GET'])
def stops(route_tag):
    route = blob.blob.get_route_by_tag(route_tag)
    stops_array = []
    for stop in route.stops:
        row = stop_to_api_dict(stop, route)
        stops_array.append(row)
    retval = json.dumps(stops_array)
    return retval


@app.route('/routes/stops', methods=['POST'])
def routes_stops():
    route_tags = request.get_json()
    for route_tag in route_tags:
        route = blob.blob.get_route_by_tag(route_tag)
        stops_array = []
        for stop in route.stops:
            row = stop_to_api_dict(stop, route)
            stops_array.append(row)
    retval = json.dumps(stops_array)
    return retval


def bigloop():
    thread = threading.Thread(target=route_vehicle_locations_loop)
    thread.start()
    route = "501"
    while 1:
        print_locations(route)
        time.sleep(30)


def main_loop():
    thread = threading.Thread(target=route_vehicle_locations_loop)
    thread.start()
    app.run(host='0.0.0.0')


def route_vehicle_locations_loop():
    vehicleLocations_update_loop(all_route_tags)


def blob_update_route(route_tag: str):
    fetched_route = get_route_details(route_tag)
    blob.blob.add_route(fetched_route)
    return


if __name__ == '__main__':
    routes = get_route_list()
    for route in routes:
        all_route_tags.append(route.tag)
    print(len(all_route_tags))
    # print('["'+'","'.join(all_route_tags) + '"]')
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        completed_futures: int = 0
        for route_tag in all_route_tags:
            futures.append(executor.submit(blob_update_route, route_tag=route_tag))
        for future in concurrent.futures.as_completed(futures):
            completed_futures += 1
            # print(f'compeleted {completed_futures}')
    main_loop()
