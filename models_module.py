

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


def print_stops(stops):
    for stop in stops:
        print("Tag:", stop.tag)
        print("Title:", stop.title)
        print("Latitude:", stop.lat)
        print("Longitude:", stop.lon)
        print("Stop ID:", stop.stop_id)
        print("-----------------------")


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
