import csv
import json

import routeconfig_module
import xml.etree.ElementTree as eT
import pyproj
import time
import requests


class Stop:
    def __init__(self, tag, title, lat, lon, stop_id):
        self.tag = tag
        self.title = title
        self.lat = lat
        self.lon = lon
        self.stop_id = stop_id


class Direction:
    def __init__(self, tag, title, name, branch):
        self.tag = tag
        self.title = title
        self.name = name
        self.branch = branch
        self.stops = []

    def add_stop(self, stop):
        self.stops.append(stop)


class VehicleLocationSnapshot:
    def __init__(self, vehicle_id, route_tag, dir_tag, lat, lon, secs_since_report, predictable, heading, speed_km_hr,
                 last_time):
        self.vehicle_id = vehicle_id
        self.route_tag = route_tag
        self.dir_tag = dir_tag
        self.lat = lat
        self.lon = lon
        self.secs_since_report = secs_since_report
        self.predictable = predictable
        self.heading = heading
        self.speed_km_hr = speed_km_hr
        self.last_time = last_time

    def __iter__(self):
        return iter([self.vehicle_id,
                     self.route_tag,
                     self.dir_tag,
                     self.lat,
                     self.lon,
                     self.secs_since_report,
                     self.predictable,
                     self.heading,
                     self.speed_km_hr,
                     self.last_time])


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.


def print_stops(stops):
    for stop in stops:
        print("Tag:", stop.tag)
        print("Title:", stop.title)
        print("Latitude:", stop.lat)
        print("Longitude:", stop.lon)
        print("Stop ID:", stop.stop_id)
        print("-----------------------")


def main():
    # Press the green button in the gutter to run the script.
    if __name__ == '__main__':
        print_hi('PyCharm')

    stops = []

    root = eT.fromstring(routeconfig_module.routeConfig)
    stop_elements = root.findall("./route/stop")

    for stop_element in stop_elements:
        stop_tag = stop_element.get("tag")
        stop_title = stop_element.get("title")
        stop_lat = float(stop_element.get("lat"))
        stop_lon = float(stop_element.get("lon"))
        stop_stop_id = stop_element.get("stopId")

        # Create and append the Stop object to the stops list
        stop_obj = Stop(stop_tag, stop_title, stop_lat, stop_lon, stop_stop_id)
        stops.append(stop_obj)

    directions = []
    direction_elements = root.findall("./route/direction")

    for direction_element in direction_elements:
        direction_obj = Direction(
            tag=direction_element.get('tag'),
            title=direction_element.get('title'),
            name=direction_element.get('name'),
            branch=direction_element.get('branch')
        )
        direction_stops_elements = direction_element.findall("./stop")
        for direction_stops_element in direction_stops_elements:
            direction_stop_obj = [stop for stop in stops if stop.tag == direction_stops_element.get("tag")][0]
            direction_obj.add_stop(direction_stop_obj)
        directions.append(direction_obj)

    last_update_time = '0'
    command = "vehicleLocations"
    route = "501"
    delay = 20
    file_period = 5 * 60 * 1000
    while True:
        vehicle_location_snapshots = []
        start_update = None
        i = 1
        while True:
            print(f'i: {i}')
            i = i + 1
            url = get_url_route_vehicle_locations(route, last_update_time)
            response = requests.get(url, headers={"Content-Type": "application/json"})
            xml = response.text
            # print(f'{xml}')
            root = eT.fromstring(xml)
            vehicle_elements = root.findall("./vehicle")
            old_last_update_time = int(last_update_time)
            last_update_time = root.find("./lastTime").get("time")
            print(f'{(int(last_update_time) - old_last_update_time) / 1000} {last_update_time} {len(vehicle_elements)}')
            if start_update is None:
                start_update = last_update_time
            for vehicle_element in vehicle_elements:
                vehicle_location_snapshot_obj = (
                    make_vehicle_location_snapshot_from_element(last_update_time, vehicle_element))
                vehicle_location_snapshots.append(vehicle_location_snapshot_obj)
            if (int(last_update_time) - int(start_update)) > file_period:
                break
            time.sleep(delay)

        filename = "c:/work/python/output/" + "vhs_" + route + "_" + start_update + "_" + last_update_time + ".csv"
        with open(filename, "w", newline='', encoding='utf-8') as stream:
            writer = csv.writer(stream)
            writer.writerows(vehicle_location_snapshots)

    # closest_stop_pairs = find_nearest_stops(xml, directions)
    #
    # for key in closest_stop_pairs:
    #     vehicle_location_snapshot = closest_stop_pairs[key]["vehicle_location_snapshot"]
    #     stop_from = closest_stop_pairs[key]["stop_from"]
    #     stop_to = closest_stop_pairs[key]["stop_to"]
    #     print(f'id:{vehicle_location_snapshot.vehicle_id} From:{stop_from.title} to To:{stop_to.title}')

    pass


def make_vehicle_location_snapshot_from_element(last_update_time, vehicle_element):
    return VehicleLocationSnapshot(
        vehicle_id=vehicle_element.get("id"),
        route_tag=vehicle_element.get("routeTag"),
        dir_tag=vehicle_element.get("dirTag"),
        lat=float(vehicle_element.get("lat")),
        lon=float(vehicle_element.get("lon")),
        secs_since_report=None if vehicle_element.get("secsSinceReport") is None else int(
            vehicle_element.get("secsSinceReport")),
        predictable=vehicle_element.get("predictable"),
        heading=None if int(vehicle_element.get("heading")) < 0 else int(vehicle_element.get("heading")),
        speed_km_hr=None if vehicle_element.get("speedKmHr") is None else int(vehicle_element.get("speedKmHr")),
        last_time=int(last_update_time)
    )


def get_url_route_vehicle_locations(route, epoch_time):
    url = 'https://webservices.umoiq.com/service/publicXMLFeed?command=vehicleLocations&a=ttc&r=' + route + '&t=' + epoch_time
    return url


def get_url_route_config(route):
    url = 'https://webservices.umoiq.com/service/publicXMLFeed?command=routeConfig&a=ttc&r=' + route
    return url


def find_nearest_stops(xml, directions):
    root = eT.fromstring(xml)
    last_time = root.find("./lastTime").get("time")
    vehicle_location_snapshots = []
    vehicle_elements = root.findall("./vehicle")
    for vehicle_element in vehicle_elements:
        vehicle_location_snapshot_obj = VehicleLocationSnapshot(
            vehicle_id=vehicle_element.get("id"),
            route_tag=vehicle_element.get("routeTag"),
            dir_tag=vehicle_element.get("dirTag"),
            lat=float(vehicle_element.get("lat")),
            lon=float(vehicle_element.get("lon")),
            secs_since_report=None if vehicle_element.get("secsSinceReport") is None else int(
                vehicle_element.get("secsSinceReport")),
            predictable=vehicle_element.get("predictable"),
            heading=None if int(vehicle_element.get("heading")) < 0 else int(vehicle_element.get("heading")),
            speed_km_hr=None if vehicle_element.get("speedKmHr") is None else int(vehicle_element.get("speedKmHr")),
            last_time=int(last_time)
        )
        vehicle_location_snapshots.append(vehicle_location_snapshot_obj)

    closest_stop_pairs = {}
    for vehicle_location_snapshot in vehicle_location_snapshots:
        vehicle_lat = vehicle_location_snapshot.lat
        vehicle_lon = vehicle_location_snapshot.lon
        vehicle_id = vehicle_location_snapshot.vehicle_id
        vehicle_dir = vehicle_location_snapshot.dir_tag
        print(f'---{vehicle_id}---')
        if vehicle_dir is None:
            print(f'skipping {vehicle_id} : no direction')
            continue
        for direction in directions:
            if direction.tag != vehicle_dir:
                continue
            stops = direction.stops
            for stop_from, stop_to in zip(stops[::1], stops[1::1]):
                # print(f'{stop_from.stop_id} {stop_from.lat} {stop_from.lon}')
                # print(f'{stop_to.stop_id} {stop_to.lat} {stop_to.lon}')
                # print(f'{vehicle_lat} {vehicle_lon}')
                inbetween = triangle_inequality(vehicle_lat, vehicle_lon, stop_from.lat, stop_from.lon, stop_to.lat,
                                                stop_to.lon)
                if vehicle_id in closest_stop_pairs:
                    if inbetween < closest_stop_pairs[vehicle_id]["inbetween"]:
                        closest_stop_pairs[vehicle_id]["vehicle_location_snapshot"] = vehicle_location_snapshot
                        closest_stop_pairs[vehicle_id]["stop_from"] = stop_from
                        closest_stop_pairs[vehicle_id]["stop_to"] = stop_to
                        closest_stop_pairs[vehicle_id]["inbetween"] = inbetween
                else:
                    closest_stop_pairs[vehicle_id] = {}
                    closest_stop_pairs[vehicle_id]["vehicle_location_snapshot"] = vehicle_location_snapshot
                    closest_stop_pairs[vehicle_id]["stop_from"] = stop_from
                    closest_stop_pairs[vehicle_id]["stop_to"] = stop_to
                    closest_stop_pairs[vehicle_id]["inbetween"] = inbetween
    return closest_stop_pairs


def before_stop(stop_of_interest, stops, vehicle_location_snapshot):
    v = vehicle_location_snapshot
    v_dir = v.dir_tag
    v_lat = v.lat
    v_lon = v.lon
    stop_index = stops.index(stop_of_interest)
    closest_stop_pair = None
    for stop_from, stop_to in zip(stops[::1], stops[1::1]):
        inbetween = triangle_inequality(v_lat, v_lon, stop_from.lat, stop_from.lon, stop_to.lat, stop_to.lon)

        if closest_stop_pair is not None:
            if inbetween < closest_stop_pair["inbetween"]:
                closest_stop_pair = {"vehicle_location_snapshot": vehicle_location_snapshot, "stop_from": stop_from,
                                     "stop_to": stop_to, "inbetween": inbetween}
        else:
            closest_stop_pair = {"vehicle_location_snapshot": vehicle_location_snapshot, "stop_from": stop_from,
                                 "stop_to": stop_to, "inbetween": inbetween}
    stop_to_index = stops.index(closest_stop_pair["stop_to"])
    return stop_to_index <= stop_index


def triangle_inequality(v_lat, v_lon, stop_from_lat, stop_from_lon, stop_to_lat, stop_to_lon):
    geodesic = pyproj.Geod(ellps='WGS84')
    _, _, distance_vehicle_from = geodesic.inv(stop_from_lon, stop_from_lat, v_lon, v_lat)
    _, _, distance_vehicle_to = geodesic.inv(stop_to_lon, stop_to_lat, v_lon, v_lat)
    _, _, distance_to_from = geodesic.inv(stop_from_lon, stop_from_lat, stop_to_lon, stop_to_lat)
    inbetween = abs(distance_to_from - (distance_vehicle_from + distance_vehicle_to))
    return inbetween


# main()

def main2():
    # Press the green button in the gutter to run the script.
    if __name__ == '__main__':
        print_hi('Main 2')

    route = "501"
    xml = request_route_config(route)
    (stops, directions) = extract_route_config(xml)
    stop = next(stop for stop in stops if stop.tag == "3399")
    print(f'{stop.title}')

    last_update_time = '0'
    delay = 20

    for i in range(100):
        # print(f'i: {i}')
        xml = request_vehicle_locations(route, last_update_time)
        last_update_time, vehicle_location_snapshots = extract_vehicle_location_snapshots(xml)

        for v in vehicle_location_snapshots:
            # if v.vehicle_id != "4582":
            #     continue
            if v.dir_tag is None:
                continue
            v_directions = [direction for direction in directions if direction.tag == v.dir_tag]
            if len(v_directions) != 0:
                v_direction = v_directions[0]
                v_stops = v_direction.stops
                if stop in v_stops:
                    report_time = int(v.last_time / 1000) - v.secs_since_report
                    before = before_stop(stop, v_stops, v)
                    row = {}
                    row['id'] = v.vehicle_id
                    row['time'] = report_time
                    row['lat'] = v.lat
                    row['lng'] = v.lon
                    row['before'] = before
                    row['dirTag'] = v.dir_tag
                    print(json.dumps(row))
            else:
                print(f'Weird: no direction {v.dir_tag}, what direction is vehicle {v.vehicle_id}on? {v.lat},{v.lon}')
                continue
        time.sleep(delay)


def extract_route_config(xml):
    stops = []
    root = eT.fromstring(xml)
    stop_elements = root.findall("./route/stop")
    for stop_element in stop_elements:
        stop_tag = stop_element.get("tag")
        stop_title = stop_element.get("title")
        stop_lat = float(stop_element.get("lat"))
        stop_lon = float(stop_element.get("lon"))
        stop_stop_id = stop_element.get("stopId")

        # Create and append the Stop object to the stops list
        stop_obj = Stop(stop_tag, stop_title, stop_lat, stop_lon, stop_stop_id)
        stops.append(stop_obj)
    directions = []
    direction_elements = root.findall("./route/direction")
    for direction_element in direction_elements:
        # print(f'Direction: {direction_element.get("tag")}')
        direction_obj = Direction(
            tag=direction_element.get('tag'),
            title=direction_element.get('title'),
            name=direction_element.get('name'),
            branch=direction_element.get('branch')
        )
        direction_stops_elements = direction_element.findall("./stop")
        for direction_stops_element in direction_stops_elements:
            direction_stop_obj = next(stop for stop in stops if stop.tag == direction_stops_element.get("tag"))
            direction_obj.add_stop(direction_stop_obj)
        directions.append(direction_obj)
    return stops, directions


def extract_vehicle_location_snapshots(xml):
    root = eT.fromstring(xml)
    vehicle_elements = root.findall("./vehicle")
    last_update_time = root.find("./lastTime").get("time")
    vehicle_locations_snapshots = []
    for vehicle_element in vehicle_elements:
        vehicle_locations_snapshot = make_vehicle_location_snapshot_from_element(last_update_time, vehicle_element)
        vehicle_locations_snapshots.append(vehicle_locations_snapshot)
    return last_update_time, vehicle_locations_snapshots


def request_vehicle_locations(route, last_update_time):
    url = get_url_route_vehicle_locations(route, last_update_time)
    response = requests.get(url, headers={"Content-Type": "application/json"})
    xml = response.text
    return xml


def request_route_config(route):
    url = get_url_route_config(route)
    response = requests.get(url, headers={"Content-Type": "application/json"})
    xml = response.text
    return xml

pass #put break point so you can have console loaded

main2()

