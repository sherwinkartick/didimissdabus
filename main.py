import concurrent
from concurrent import futures
import json
import threading
import time
from typing import List
from geopy import distance

from flask import Flask, request
from flask_cors import CORS

import mathy_module as mathy
import models_module as mm
import request_and_parsing_module as rpm
import statesman_module as blob

app = Flask(__name__)
CORS(app)


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
    # print(f'compeleted {route_tag} {len(vehicle_location_snapshots)}')
    blob.blob.add_vls(vehicle_location_snapshots)
    return route_tag, last_update_time


def vehicleLocations_update_loop(all_route_tags: List[str], monitored_route_tags: List[str]):
    last_update_routes_time = 0
    update_routes_delay = 15 * 60
    last_update_times = {}
    delay = 15
    for monitored_route_tag in monitored_route_tags:
        last_update_times[monitored_route_tag] = '0'
    while 1:
        start_time = int(time.time())
        if (start_time - last_update_routes_time) > update_routes_delay:
            print(f'Updating routes {start_time}')
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futuresa = []
                for route_tag in all_route_tags:
                    futuresa.append(executor.submit(blob_update_route, route_tag=route_tag))
                for _ in concurrent.futures.as_completed(futuresa):
                    pass
            blob.blob.init_stops()
            last_update_routes_time = int(time.time())
            print(f'Finished updating routes {last_update_routes_time}')

        if len(monitored_route_tags) > 0:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futuresa = []
                for route_tag in monitored_route_tags:
                    futuresa.append(executor.submit(blob_update_vlss, route_tag=route_tag,
                                                    last_update_time=last_update_times[route_tag]))
                for future in concurrent.futures.as_completed(futuresa):
                    route_tag, last_update_time = future.result()
                    last_update_times[route_tag] = last_update_time
        print(f'Finished updating locations {time.ctime()}')
        end_time = int(time.time())
        total_time = end_time - start_time
        # print(f'Loop time: {total_time}')
        if delay - total_time > 0:
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
    row['id'] = vls.id_
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


def stop_to_api_dict(unique_stop: mm.UniqueStop):
    row = {}
    row['tag'] = unique_stop.tag
    row['title'] = unique_stop.title
    row['lat'] = unique_stop.lat
    row['lng'] = unique_stop.lon
    # row['stopId'] = unique_stop.stopId
    # row['dirName'] = unique_stop.route_directions[0].name
    # row['routeTag'] = unique_stop.routes[0].tag
    return row


def get_dir_name(route_stop: mm.RouteStop):
    retval = None
    route : mm.Route = route_stop.route
    route_direction: mm.RouteDirection
    for route_direction in route.route_directions:
        for route_direction_stop in route_direction.route_stops:
            if route_direction_stop.tag == route_stop.tag:
                retval = route_direction.name
                return retval
    return retval


def print_stops(route_tags: List[str]):
    for route_tag in route_tags:
        route = blob.blob.get_route_by_tag(route_tag)
        for stop in route.route_stops:
            row = stop_to_api_dict(stop, route)
            print(json.dumps(row))


@app.route('/stops/<route>', methods=['GET'])
def route_stops(route_tag):
    route = blob.blob.get_route_by_tag(route_tag)
    stops_array = []
    for stop in route.route_stops:
        row = stop_to_api_dict(stop, route)
        stops_array.append(row)
    retval = json.dumps(stops_array)
    return retval


@app.route('/stops/nearest', methods=['POST'])
def stops_nearest():
    stop_coord_json = request.get_json()
    stop_coord = (stop_coord_json["lat"], stop_coord_json["lng"])
    nearest_stops_to_coord = nearest_stops(stop_coord)
    stops_array = []
    for nearest_stop in nearest_stops_to_coord:
        for route in nearest_stop.routes:
            has_vehicles = False
            if route.tag in blob.blob.latest_vls:
                has_vehicles = True
                break
        if has_vehicles:
            row = stop_to_api_dict(nearest_stop)
            stops_array.append(row)
    retval = json.dumps(stops_array)
    return retval

def main_loop(all_route_tags: List[str], monitored_route_tags: List[str]):
    thread = threading.Thread(target=vehicleLocations_update_loop, args=(all_route_tags, monitored_route_tags))
    thread.start()
    app.run(host='0.0.0.0')


def blob_update_route(route_tag: str):
    fetched_route = get_route_details(route_tag)
    blob.blob.add_route(fetched_route)
    return


def main():
    routes = get_route_list()
    all_route_tags = []
    for route in routes:
        all_route_tags.append(route.tag)
    monitored_route_tags = ["301", "307", "501", "511"]
    main_loop(all_route_tags, monitored_route_tags)


def module_stuff():
    routes = get_route_list()
    all_route_tags = []
    for route in routes:
        all_route_tags.append(route.tag)
    monitored_route_tags = ["301", "307", "501", "511"]
    thread = threading.Thread(target=vehicleLocations_update_loop, args=(all_route_tags, monitored_route_tags))
    thread.start()
    return


def experiment():
    module_stuff()
    time.sleep(10)  # shit to start up
    node = (43.647646, -79.406242)
    stops = nearest_stops(node)
    for stop in stops:
        for route in stop.routes:
            has_vehicles = False
            if route.tag in blob.blob.latest_vls:
                has_vehicles = True
                break
        if has_vehicles:
            print(stop.title)



def nearest_stops(coord, num_stops=10):
    stops = blob.blob.unique_stops
    unique_stop: mm.UniqueStop
    distances = {}
    for _, unique_stop in stops.items():
        stop_distance = distance.distance(coord, (unique_stop.lat, unique_stop.lon)).m
        distances[stop_distance] = unique_stop
    min_distances = list(distances.keys())
    min_distances.sort()
    retval : List[mm.UniqueStop] = []
    for i in range(0,num_stops):
        retval.append(distances[min_distances[i]])
    return retval


if __name__ == '__main__':
    main()
    # experiment()
