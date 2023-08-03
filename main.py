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
    delay = 10
    for i in range(100):
        print(f'i: {i}')
        url = get_url_route_vehicle_locations(command, last_update_time, route)
        response = requests.get(url, headers={"Content-Type": "application/json"})
        xml = response.text
        #print(f'{xml}')
        root = eT.fromstring(xml)
        vehicle_elements = root.findall("./vehicle")
        print(f'{last_update_time} {len(vehicle_elements)}')
        last_update_time = str(int(time.time()*1000)) #root.find("./lastTime").get("time")
        time.sleep(delay)


    # closest_stop_pairs = find_nearest_stops(xml, directions)
    #
    # for key in closest_stop_pairs:
    #     vehicle_location_snapshot = closest_stop_pairs[key]["vehicle_location_snapshot"]
    #     stop_from = closest_stop_pairs[key]["stop_from"]
    #     stop_to = closest_stop_pairs[key]["stop_to"]
    #     print(f'id:{vehicle_location_snapshot.vehicle_id} From:{stop_from.title} to To:{stop_to.title}')

    pass


def get_url_route_vehicle_locations(command, epoch_time, route):
    url = 'https://webservices.umoiq.com/service/publicXMLFeed?command=' + command + '&a=ttc' + '&r=' + route + '&t=' + epoch_time
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
    geodesic = pyproj.Geod(ellps='WGS84')
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

                _, _, distance_vehicle_from = geodesic.inv(stop_from.lon, stop_from.lat, vehicle_lon, vehicle_lat)
                _, _, distance_vehicle_to = geodesic.inv(stop_to.lon, stop_to.lat, vehicle_lon, vehicle_lat)
                _, _, distance_to_from = geodesic.inv(stop_from.lon, stop_from.lat, stop_to.lon, stop_to.lat)
                inbetween = abs(distance_to_from - (distance_vehicle_from + distance_vehicle_to))
                print(f'{inbetween} {stop_from.stop_id} {stop_to.stop_id} ')
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


main()
