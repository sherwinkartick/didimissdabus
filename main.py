import json
import threading
import time

from flask import Flask
from flask_cors import CORS

import mathy_module as mathy
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


def vls_update_loop(route):
    last_update_time = '0'
    delay = 20
    for i in range(100):
        vehicle_location_snapshots = get_latest_vehicle_locations(last_update_time, route)
        for vls in vehicle_location_snapshots:
            blob.blob.add_vls(vls)
        time.sleep(delay)


def get_latest_vehicle_locations(last_update_time, route):
    xml = rpm.request_vehicle_locations(route, last_update_time)
    last_update_time, vehicle_location_snapshots = rpm.extract_vehicle_location_snapshots(xml)
    return vehicle_location_snapshots


def get_stop_from_directions(stop_tag, stops):
    stop = next(stop for stop in stops if stop.tag == stop_tag)
    return stop


def get_route_details(route):
    xml = rpm.request_route_config(route)
    (stops, directions) = rpm.extract_route_config(xml)
    return directions, stops


def print_locations(route):
    vlss = blob.blob.get_latest(route)
    for vls in vlss:
        report_time = int(vls.last_time / 1000) - vls.secs_since_report
        row = {}
        row['id'] = vls.vehicle_id
        row['time'] = report_time
        row['lat'] = vls.lat
        row['lng'] = vls.lon
        row['dirTag'] = vls.dir_tag
        row['routeTag'] = vls.route_tag
        row['heading'] = vls.heading
        row['speed'] = vls.speed_km_hr
        print(json.dumps(row))


@app.route('/locations/<route>', methods=['GET'])
def locations501(route):
    vlss = blob.blob.get_latest(route)
    locations_array = []
    for vls in vlss:
        report_time = int(vls.last_time / 1000) - vls.secs_since_report
        print(f'Time: {int(time.time()) - report_time}')
        row = {}
        row['id'] = vls.vehicle_id
        row['time'] = report_time
        row['lat'] = vls.lat
        row['lng'] = vls.lon
        row['dirTag'] = vls.dir_tag
        row['routeTag'] = vls.route_tag
        row['heading'] = vls.heading
        row['speed'] = vls.speed_km_hr
        locations_array.append(row)
    retval = json.dumps(locations_array)
    return retval

def bigloop():
    thread = threading.Thread(target=smallloop)
    thread.start()
    route = "501"
    for i in range(100):
        print_locations(route)
        time.sleep(30)


def bigloop2():
    thread = threading.Thread(target=smallloop)
    thread.start()
    app.run()



def smallloop():
    vls_update_loop("501")


pass  # put break point so you can have console loaded
# output_direction_locations_json()
bigloop2()
