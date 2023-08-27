import xml.etree.ElementTree as eT

import requests

import models_module as mm


def extract_route_config(xml):

    root = eT.fromstring(xml)
    route_element = root.find("./route")
    route_tag = route_element.get("tag")
    route_title = route_element.get("title")
    route_latMin = float(route_element.get("latMin"))
    route_latMax = float(route_element.get("latMax"))
    route_lonMin = float(route_element.get("lonMin"))
    route_lonMax = float(route_element.get("lonMax"))

    path_elements = route_element.findall("./path")
    paths = []
    for path_element in path_elements:
        tags = []
        tag_elements = path_element.findall("./tag")
        for tag_element in tag_elements:
            tag_id = tag_element.get("id")
            tag = mm.Tag(tag_id)
            tags.append(tag)
        points = []
        point_elements = path_element.findall("./point")
        for point_element in point_elements:
            point_lat = float(point_element.get("lat"))
            point_lon = float(point_element.get("lon"))
            point = mm.Point(point_lat, point_lon)
            points.append(point)
        path = mm.Path(tags, points)
        paths.append(path)
    route = mm.Route(route_tag, route_title, route_latMin, route_latMax, route_lonMin, route_lonMax, paths)

    route_stops = []
    stops_tag = {}
    stop_elements = root.findall("./route/stop")
    for stop_element in stop_elements:
        stop_tag = stop_element.get("tag")
        stop_title = stop_element.get("title")
        stop_lat = float(stop_element.get("lat"))
        stop_lon = float(stop_element.get("lon"))
        stop_stopId = stop_element.get("stopId")
        stop_obj = mm.RouteStop(route, stop_tag, stop_title, stop_lat, stop_lon, stop_stopId)
        stops_tag[stop_tag] = stop_obj
        route_stops.append(stop_obj)
    route.route_stops = route_stops

    route_directions = []
    direction_elements = root.findall("./route/direction")
    for direction_element in direction_elements:
        # print(f'Direction: {direction_element.get("tag")}')
        direction_tag = direction_element.get('tag')
        direction_title = direction_element.get('title')
        direction_name = direction_element.get('name')
        direction_branch = direction_element.get('branch')
        direction_useForUI = bool(direction_element.get('useForUI'))
        direction_stops_elements = direction_element.findall("./stop")
        direction_stops = []
        for direction_stops_element in direction_stops_elements:
            stop_tag = direction_stops_element.get('tag')
            direction_stop_obj = stops_tag[stop_tag]
            direction_stops.append(direction_stop_obj)
        direction_obj = mm.RouteDirection(route, direction_tag, direction_title, direction_name, direction_branch,
                                          direction_useForUI, direction_stops)
        route_directions.append(direction_obj)
    route.route_directions = route_directions

    return route


def extract_vehicle_location_snapshots(xml):
    root = eT.fromstring(xml)
    vehicle_elements = root.findall("./vehicle")
    lastTimeElement = root.find("./lastTime")
    # print(f'{len(vehicle_elements)} {lastTimeElement is None}')
    last_update_time = lastTimeElement.get("time")
    vehicle_locations_snapshots = []
    for vehicle_element in vehicle_elements:
        vehicle_locations_snapshot = mm.make_vehicle_location_snapshot_from_element(last_update_time, vehicle_element)
        vehicle_locations_snapshots.append(vehicle_locations_snapshot)
    return last_update_time, vehicle_locations_snapshots


def extract_route_list(xml):
    root = eT.fromstring(xml)
    route_elements = root.findall("./route")
    routes = []
    for route_element in route_elements:
        route_tag = route_element.get("tag")
        route_title = route_element.get("title")
        route = mm.Route(route_tag, route_title, 0.0, 0.0, 0.0, 0.0, [])
        routes.append(route)
    return routes


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


def request_route_list():
    url = get_url_route_list()
    response = requests.get(url, headers={"Content-Type": "application/json"})
    xml = response.text
    return xml


def get_url_route_vehicle_locations(route, epoch_time):
    prefix = 'https://webservices.umoiq.com/service/publicXMLFeed'
    url = prefix + '?command=vehicleLocations&a=ttc&r=' + route + '&t=' + epoch_time
    return url


def get_url_route_config(route):
    prefix = 'https://webservices.umoiq.com/service/publicXMLFeed'
    url = prefix + '?verbose&command=routeConfig&a=ttc&r=' + route
    return url


def get_url_route_list():
    url = 'http://webservices.umoiq.com/service/publicXMLFeed?command=routeList&a=ttc'
    return url
