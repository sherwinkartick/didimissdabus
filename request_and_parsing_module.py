import json
import xml.etree.ElementTree as eT

import requests

import models_module as mm


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
        stop_obj = mm.Stop(stop_tag, stop_title, stop_lat, stop_lon, stop_stop_id)
        stops.append(stop_obj)
    directions = []
    direction_elements = root.findall("./route/direction")
    for direction_element in direction_elements:
        # print(f'Direction: {direction_element.get("tag")}')
        direction_obj = mm.Direction(tag=direction_element.get('tag'), title=direction_element.get('title'),
                                     name=direction_element.get('name'), branch=direction_element.get('branch'))
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
        vehicle_locations_snapshot = mm.make_vehicle_location_snapshot_from_element(last_update_time, vehicle_element)
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


def get_url_route_vehicle_locations(route, epoch_time):
    prefix = 'https://webservices.umoiq.com/service/publicXMLFeed'
    url = prefix + '?command=vehicleLocations&a=ttc&r=' + route + '&t=' + epoch_time
    return url


def get_url_route_config(route):
    prefix = 'https://webservices.umoiq.com/service/publicXMLFeed'
    url = prefix + '?terse&command=routeConfig&a=ttc&r=' + route
    return url
