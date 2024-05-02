import concurrent
import json
import pickle
import threading
import time
from concurrent import futures
from typing import List

import numpy as np
from flask import Flask, request, make_response
from flask_cors import CORS

import mathy_module as mathy
import models_module as mm
import request_and_parsing_module as rpm
import statesman_module as blob

app = Flask(__name__)
CORS(app)


@app.after_request
def after_request_func(data):
    response = make_response(data)
    response.headers['Content-Type'] = 'application/json'
    return response


def blob_update_vlss(route_tag: str, last_update_time: str):
    last_update_time, vehicle_location_snapshots = get_latest_vehicle_locations(last_update_time, route_tag)
    # print(f'completed {route_tag} {len(vehicle_location_snapshots)}')
    blob.blob.add_vls(vehicle_location_snapshots)
    blob.blob.update_direction_vls(route_tag)
    return route_tag, last_update_time


def vehicleLocations_update_loop(all_route_tags: List[str], monitored_route_tags: List[str]):
    last_update_routes_time = 0
    update_routes_delay = 15 * 60
    last_update_times = {}
    delay = 21 # rate limit is 2MB/20sec, so 21 second pause should prevent twice in a window
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
            # print(f'Finished updating routes {last_update_routes_time}')

        if len(monitored_route_tags) > 0:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futuresa = []
                for route_tag in monitored_route_tags:
                    futuresa.append(executor.submit(blob_update_vlss, route_tag=route_tag,
                                                    last_update_time=last_update_times[route_tag]))
                for future in concurrent.futures.as_completed(futuresa):
                    route_tag, last_update_time = future.result()
                    last_update_times[route_tag] = last_update_time
        # print(f'Finished updating locations {time.ctime()}')
        end_time = int(time.time())
        total_time = end_time - start_time
        # print(f'Loop time: {total_time}')
        if delay - total_time > 0:
            time.sleep(delay - total_time)


def vehicleLocations_expire_loop():
    delay = 15
    expiry_secs = 120
    while 1:
        start_time = int(time.time())
        # print(f'Expiring: {start_time}')
        a: dict[str, dict[str, mm.VehicleLocationSnapshot]]
        for a in blob.blob.latest_vls.values():
            b: mm.VehicleLocationSnapshot
            for b in list(a.values()):
                report_time = int(b.last_time / 1000) - b.secsSinceReport
                delta_time = int(time.time()) - report_time
                if delta_time > expiry_secs:
                    # print(f'Removing {b.id_} {delta_time}')
                    del a[str(b.id_)]
                # else:
                #     print(f'Not Removing {b.id_} {delta_time}')

        c: dict[str, List[mm.VehicleLocationSnapshot]]
        for c in blob.blob.latest_direction_vls.values():
            d: List[mm.VehicleLocationSnapshot]
            for d in c.values():
                e: mm.VehicleLocationSnapshot
                for e in list(d):
                    report_time = int(e.last_time / 1000) - e.secsSinceReport
                    delta_time = int(time.time()) - report_time
                    if delta_time > expiry_secs:
                        # print(f'direction Removing {e.id_} {delta_time}')
                        d.remove(e)
                    # else:
                    #     print(f'direction Not Removing {e.id_} {delta_time}')
        end_time = int(time.time())
        total_time = end_time - start_time
        if delay - total_time > 0:
            time.sleep(delay - total_time)


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


def point_to_api_dict(point: mm.Point):
    row = {}
    row['lat'] = point.lat
    row['lng'] = point.lon
    return row


def print_locations(route):
    vlss = blob.blob.get_latest(route)
    for vls in vlss:
        row = vls_to_api_dict(vls)
        print(json.dumps(row))


@app.route('/routes/locations', methods=['POST'])
def app_routes_locations():
    request_json = request.get_json()
    locations_array = []
    for route in request_json:
        vlss = blob.blob.get_latest(route)
        for vls in vlss:
            row = vls_to_api_dict(vls)
            locations_array.append(row)  # print(json.dumps(row))
    retval = json.dumps(locations_array)
    return retval


@app.route('/route/direction/locations', methods=['POST'])
def app_route_directions_locations():
    request_json = request.get_json()
    route_tag = request_json["route_tag"]
    route_direction_tag = request_json["direction_tag"]
    latest_direction_vls = blob.blob.latest_direction_vls[route_tag]
    vlss = latest_direction_vls[route_direction_tag]
    locations_array = []
    for vls in vlss:
        row = vls_to_api_dict(vls)
        locations_array.append(row)
    retval = json.dumps(locations_array)
    return retval


@app.route('/route/direction/stops', methods=['POST'])
def app_route_direction_stops():
    request_json = request.get_json()
    route_tag = request_json["route_tag"]
    route_direction_tag = request_json["direction_tag"]
    stops_array = []
    route: mm.Route = blob.blob.get_route_by_tag(route_tag)
    route_direction: mm.RouteDirection
    for route_direction in route.route_directions:
        if route_direction.tag != route_direction_tag:
            continue
        for route_stop in route_direction.route_stops:
            row = stop_to_api_dict(route_stop)
            # print(json.dumps(row))
            stops_array.append(row)
    retval = json.dumps(stops_array)
    return retval


def stop_to_api_dict(unique_stop):
    row = {}
    row['tag'] = unique_stop.tag
    row['title'] = unique_stop.title
    row['lat'] = unique_stop.lat
    row['lng'] = unique_stop.lon
    # row['stopId'] = unique_stop.stopId
    # row['dirName'] = unique_stop.route_directions[0].name
    # row['routeTag'] = unique_stop.routes[0].tag
    return row


@app.route('/stops/nearest', methods=['POST'])
def app_stops_nearest():
    request_json = request.get_json()
    coord = (request_json["lat"], request_json["lng"])
    unique_stops = nearest_useful_stops(coord)
    direction_dict = {}
    for unique_stop in unique_stops:
        row = stop_to_api_dict(unique_stop)
        useful_directions = useful_directions_for_stop(unique_stop)
        route_directions_row = []
        for useful_direction in useful_directions:
            route_direction_row = {}
            route_direction_row['route_tag'] = useful_direction.route.tag
            route_direction_row['direction_tag'] = useful_direction.tag
            route_directions_row.append(route_direction_row)
        row['route_directions'] = route_directions_row
        key = ",".join(sorted(direction.tag for direction in useful_directions))
        # row['direction_group'] = key
        if key not in direction_dict:
            direction_dict[key] = []
        direction_dict[key].append(row)
        if len(direction_dict) == 9:
            break
    stops_array = []
    for key in direction_dict:
        for api_stop in direction_dict[key]:
            stops_array.append(api_stop)
    retval = json.dumps(stops_array)
    return retval


def nearest_useful_stops(stop_coord):
    nearest_stops_to_coord = ball_query_stops_nearest_coord(stop_coord, 30)
    useful_stops = []
    for nearest_stop in nearest_stops_to_coord:
        has_vehicles = False
        for route in nearest_stop.routes:
            if route.tag in blob.blob.latest_vls:
                for vls in blob.blob.latest_vls[route.tag].values():
                    # print(f'{vls.id_} stop tag:{nearest_stop.tag} vehicle last stop tag {blob.blob.get_direction_by_tag(vls.dirTag).route_stops[-1].tag}')
                    if nearest_stop.tag == blob.blob.get_direction_by_tag(vls.dirTag).route_stops[-1].tag:
                        continue
                    if any(vls.dirTag == route_direction.tag for route_direction in nearest_stop.route_directions):
                        # print(f'{vls.id_} {vls.dirTag} {",".join(route_direction.tag for route_direction in nearest_stop.route_directions)}')
                        has_vehicles = True
                        break
            if has_vehicles:
                useful_stops.append(nearest_stop)
                break
    return useful_stops


def useful_directions_for_stop(unique_stop: mm.UniqueStop):
    useful_directions = []
    for direction in unique_stop.route_directions:
        if direction.route.tag not in blob.blob.latest_direction_vls:
            continue
        if unique_stop.tag == direction.route_stops[-1].tag:
            continue
        route_dict = blob.blob.latest_direction_vls[direction.route.tag]
        if direction.tag in route_dict:
            useful_directions.append(direction)
    return useful_directions


@app.route('/stop/vehicles/before/<stop_tag>', methods=['GET'])
def app_stop_vehicles_before(stop_tag):
    unique_stop = blob.blob.unique_stops[stop_tag]
    routes = unique_stop.routes
    useful = []
    # print(", ".join(direction.tag for direction in unique_stop.route_directions))
    # print()
    for route in routes:
        vlss: List[mm.VehicleLocationSnapshot]
        if route.tag not in blob.blob.latest_vls:
            continue
        vlss = blob.blob.latest_vls[route.tag].values()
        for vls in vlss:
            # print(f'{vls.id_} {vls.dirTag}')
            route_direction = next(
                (direction for direction in unique_stop.route_directions if direction.tag == vls.dirTag), None)
            if route_direction is not None:
                if route_direction.route_stops[-1].tag != unique_stop.tag:
                    useful.append(vls)
    locations_array = []
    for useful_vehicle in useful:
        before, num_stops_away = mathy.before_stop_and_by_how_many(unique_stop, useful_vehicle)
        if before == "before_stop":
            # print(f'{useful_vehicle.id_} {useful_vehicle.dirTag} {before} {num_stops_away}')
            row = vls_to_api_dict(useful_vehicle)
            # print(row)
            row["number_stops_away"] = num_stops_away
            locations_array.append(row)
    retval = json.dumps(locations_array)
    # print(retval)
    return retval


@app.route('/route/direction/path', methods=['POST'])
def app_route_direction_path():
    request_json = request.get_json()
    route_tag = request_json["route_tag"]
    route_direction_tag = request_json["direction_tag"]
    route: mm.Route = blob.blob.get_route_by_tag(route_tag)
    points = []
    for path in route.paths:
        for tag in path.tags:
            if tag.id_.startswith(route_direction_tag + '_'):
                points.append(path.points)
    points_array = []
    for i in range(len(points)):
        for point in points[i]:
            row = point_to_api_dict(point)
            row['index'] = i
            points_array.append(row)
            # print(json.dumps(row))
    retval = json.dumps(points_array)
    return retval


def ball_query_stops_nearest_coord(coord, num_stops=10):
    retval: List[mm.UniqueStop] = []
    if blob.blob.ball_tree is None:
        return retval
    lat = float(coord[0]) * np.pi / 180
    lon = float(coord[1]) * np.pi / 180
    distances, indices = blob.blob.ball_tree.query(np.array([[lat, lon]]), k=num_stops)
    unique_stops = list(blob.blob.unique_stops.values())
    i = 0
    for index in indices[0]:
        distance_to_stop = distances[0][i] * 6371
        i += 1
        if distance_to_stop > 1:  # limit to 1km radius, probably should make a parameter
            continue
        retval.append(unique_stops[index])
    return retval


def main_loop(all_route_tags: List[str], monitored_route_tags: List[str]):
    thread1 = threading.Thread(target=vehicleLocations_update_loop, args=(all_route_tags, monitored_route_tags))
    thread1.start()
    thread2 = threading.Thread(target=vehicleLocations_expire_loop)
    thread2.start()
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
    monitored_route_tags = ['501', '503', '504', '505', '506', '507', '508', '509', '510', '511', '512']
    main_loop(all_route_tags, monitored_route_tags) # avoiding rate limiting, so just doing primarily 'streetcar' routes


def module_stuff():
    routes = get_route_list()
    all_route_tags = []
    for route in routes:
        all_route_tags.append(route.tag)
    monitored_route_tags = ["301", "307", "501", "511"]
    thread = threading.Thread(target=vehicleLocations_update_loop, args=(all_route_tags, monitored_route_tags))
    thread.start()
    return


def save_state():
    module_stuff()
    time.sleep(10)  # shift to start up
    with open('data.pkl', 'wb') as file:
        pickle.dump(blob.blob, file)
    return


def experiment():
    with open('data.pkl', 'rb') as file:
        blob.blob = pickle.load(file)
    # coord = (43.64763175446401, -79.40623827336564)
    return


if __name__ == '__main__':
    main()
    # save_state()
    # experiment()
