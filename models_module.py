from __future__ import annotations

from typing import List


class Route:
    def __init__(self, tag: str, title: str, latMin: float, latMax: float, lonMin: float, lonMax: float,
                 paths: List[Path]):
        self.tag = tag
        self.title = title
        self.latMin = latMin
        self.latMax = latMax
        self.lonMin = lonMin
        self.lonMax = lonMax
        self.paths = paths
        self.route_stops = []
        self.route_directions = []


class Path:
    def __init__(self, tags: List[Tag], points: List[Point]):
        self.tags = tags
        self.points = points


class Tag:
    def __init__(self, id_: str):
        self.id_ = id_


class Point:
    def __init__(self, lat: float, lon: float):
        self.lat = lat
        self.lon = lon


class RouteStop:
    def __init__(self, route: Route, tag: str, title: str, lat: float, lon: float, stopId: str):
        self.tag = tag
        self.title = title
        self.lat = lat
        self.lon = lon
        self.stopId = stopId
        self.route = route


class RouteDirection:
    def __init__(self, route: Route, tag: str, title: str, name: str, branch: str,
                 useForUI: bool, route_stops: List[RouteStop]):
        self.route = route
        self.tag = tag
        self.title = title
        self.name = name
        self.branch = branch
        self.route_stops = route_stops
        self.useForUI = useForUI


class VehicleLocationSnapshot:
    def __init__(self, id_: int, routeTag: str, dirTag: str, lat: float, lon: float, secsSinceReport: int, predictable,
                 heading: float, speedKmHr: int, last_time: int):
        self.id_ = id_
        self.routeTag = routeTag
        self.dirTag = dirTag
        self.lat = lat
        self.lon = lon
        self.secsSinceReport = secsSinceReport
        self.predictable = predictable
        self.heading = heading
        self.speedKmHr = speedKmHr
        self.last_time = last_time


class UniqueStop:
    def __init__(self, tag: str, title: str, lat: float, lon: float, stopId: str):
        self.tag = tag
        self.title = title
        self.lat = lat
        self.lon = lon
        self.stopId = stopId
        self.routes = []
        self.route_directions = []

    def add_route(self, route: Route):
        self.routes.append(route)

    def add_route_direction(self, route_direction: RouteDirection):
        self.route_directions.append(route_direction)

def make_vehicle_location_snapshot_from_element(last_update_time: str, vehicle_element):
    id_ = vehicle_element.get("id")
    routeTag = vehicle_element.get("routeTag")
    dirTag = vehicle_element.get("dirTag")
    lat = float(vehicle_element.get("lat"))
    lon = float(vehicle_element.get("lon"))
    secsSinceReport = None if vehicle_element.get("secsSinceReport") is None else int(
        vehicle_element.get("secsSinceReport"))
    predictable = vehicle_element.get("predictable"),
    heading = None if int(vehicle_element.get("heading")) < 0 else int(vehicle_element.get("heading"))
    speedKmHr = None if vehicle_element.get("speedKmHr") is None else int(vehicle_element.get("speedKmHr"))
    last_time = int(last_update_time)
    vls = VehicleLocationSnapshot(id_, routeTag, dirTag, lat, lon, secsSinceReport, predictable, heading, speedKmHr,
                                  last_time)
    return vls
