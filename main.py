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
    def __init__(self, tag, title, name, use_for_ui, branch):
        self.tag = tag
        self.title = title
        self.name = name
        self.use_for_ui = use_for_ui
        self.branch = branch
        self.stops = []

    def add_stop(self, stop):
        self.stops.append(stop)


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

    root = eT.fromstring(routeconfig_module.routeConfig)
    stop_elements = root.findall("./route/stop")

    stops = []

    for stop_element in stop_elements:
        stop_tag = stop_element.get("tag")
        stop_title = stop_element.get("title")
        stop_lat = float(stop_element.get("lat"))
        stop_lon = float(stop_element.get("lon"))
        stop_stop_id = stop_element.get("stopId")

        # Create and append the Stop object to the stops list
        stop_obj = Stop(stop_tag, stop_title, stop_lat, stop_lon, stop_stop_id)
        stops.append(stop_obj)

    print_stops(stops)


main()
