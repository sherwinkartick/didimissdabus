import routeconfig_module
import vehiclelocations_module
import xml.etree.ElementTree as eT


class Stop:
    def __init__(self, tag, title, lat, lon, stop_id):
        self.tag = tag
        self.title = title
        self.lat = lat
        self.lon = lon
        self.stopId = stop_id


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
        print("Stop ID:", stop.stopId)
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

    root = eT.fromstring(vehiclelocations_module.vehicleLocations)
    last_time = root.find("./lastTime").get("time")

    vehicle_location_snapshots = []
    vehicle_elements = root.findall("./vehicle")
    for vehicle_element in vehicle_elements:
        vehicle_location_snapshot_obj = VehicleLocationSnapshot(
            vehicle_id=vehicle_element.get("vehicle_id"),
            route_tag=vehicle_element.get("route_tag"),
            dir_tag=vehicle_element.get("dir_tag"),
            lat=vehicle_element.get("lat"),
            lon=vehicle_element.get("lon"),
            secs_since_report=vehicle_element.get("secs_since_report"),
            predictable=vehicle_element.get("predictable"),
            heading=vehicle_element.get("heading"),
            speed_km_hr=vehicle_element.get("speed_km_hr"),
            last_time=last_time
        )
        vehicle_location_snapshots.append(vehicle_location_snapshot_obj)
    print(len(vehicle_location_snapshots))
    pass


main()

