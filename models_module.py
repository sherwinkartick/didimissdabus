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
        self.stops = []
        self.directions = []

    def add_stops(self, stops: List[Stop]):
        self.stops.extend(stops)

    def add_directions(self, directions: List[Direction]):
        self.directions.extend(directions)


class Path:
    def __init__(self, tags: List[Tag], points: List[Point]):
        self.tags = tags
        self.points = points


class Tag:
    def __init__(self, id: str):
        self.id = id


class Point:
    def __init__(self, lat: float, lon: float):
        self.lat = lat
        self.lon = lon


class Stop:
    def __init__(self, tag: str, title: str, lat: float, lon: float, stopId: str):
        self.tag = tag
        self.title = title
        self.lat = lat
        self.lon = lon
        self.stopId = stopId
        self.directions = []
        self.routes = []

    def add_direction(self, direction: Direction):
        self.directions.append(direction)

    def add_route(self, route: Route):
        self.routes.append(route)


class Direction:
    def __init__(self, route: Route, tag: str, title: str, name: str, branch: str, useForUI:bool, stops: List[Stop]):
        self.route = route
        self.tag = tag
        self.title = title
        self.name = name
        self.branch = branch
        self.stops = stops
        self.useForUI = useForUI


class VehicleLocationSnapshot:
    def __init__(self, id: int, routeTag: str, dirTag: str, lat: float, lon: float, secsSinceReport: int, predictable,
                 heading: float, speedKmHr: int, last_time: int):
        self.id = id
        self.routeTag = routeTag
        self.dirTag = dirTag
        self.lat = lat
        self.lon = lon
        self.secsSinceReport = secsSinceReport
        self.predictable = predictable
        self.heading = heading
        self.speedKmHr = speedKmHr
        self.last_time = last_time


def make_vehicle_location_snapshot_from_element(last_update_time: str, vehicle_element):
    id = vehicle_element.get("id")
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
    vls = VehicleLocationSnapshot(id, routeTag, dirTag, lat, lon, secsSinceReport, predictable, heading, speedKmHr,
                                  last_time)
    return vls
