import time
from typing import List

import models_module as mm
from models_module import VehicleLocationSnapshot, UniqueStop
from sklearn.neighbors import BallTree
import numpy as np


class DaBlob:

    def __init__(self):
        self.unique_stops = None
        self.latest_vls = {}
        self.latest_direction_vls = {}
        self.__routes = {}
        self.__direction_tag = {}
        self.ball_tree = None

    def add_route(self, route: mm.Route):
        self.__routes[route.tag] = route
        for _,direction in self.__direction_tag.items():
            if direction.route.tag == route.tag:
                del self.__direction_tag[route.tag]
        for direction in route.route_directions:
            self.__direction_tag[direction.tag] = direction

    def init_stops(self):
        unique_stops: dict[str, UniqueStop] = {}
        route: mm.Route
        for _,route in self.__routes.items():
            # print(f'{route.tag}')
            route_stop: mm.RouteStop
            for route_stop in route.route_stops:
                route_stop_tag = route_stop.tag
                if route_stop_tag not in unique_stops:
                    unique_stop = mm.UniqueStop(route_stop.tag, route_stop.title, route_stop.lat, route_stop.lon,
                                                route_stop.stopId)
                    unique_stops[route_stop_tag] = unique_stop
                else:
                    unique_stop = unique_stops[route_stop_tag]
                unique_stop.add_route(route)
                route_direction: mm.RouteDirection
                for route_direction in route.route_directions:
                    for route_direction_stop in route_direction.route_stops:
                        if route_direction_stop.tag == unique_stop.tag:
                            unique_stop.add_route_direction(route_direction)
                            break
        self.unique_stops = unique_stops
        unique_stops_array = list(unique_stops.values())
        latitudes = np.array([obj.lat for obj in unique_stops_array])
        latitudes *= np.pi / 180
        longitudes = np.array([obj.lon for obj in unique_stops_array])
        longitudes *= np.pi / 180
        coordinates = np.column_stack((latitudes, longitudes))
        self.ball_tree = BallTree(coordinates, metric='haversine')
        return

    def add_vls(self, vlss: List[mm.VehicleLocationSnapshot]):
        vls: VehicleLocationSnapshot
        for vls in vlss:
            route_tag = vls.routeTag
            v_id = vls.id_
            dir_tag = vls.dirTag

            # dict.setdefault(key,[]).append(value), chaining is trouble though
            if route_tag not in self.latest_vls:
                self.latest_vls[route_tag] = {}

            route_latest_vls = self.latest_vls[route_tag]
            if dir_tag is None:
                if v_id in route_latest_vls:
                    # print(f'deleting {v_id}')
                    del route_latest_vls[v_id]
            else:
                # if v_id not in route_map:
                #     print(f'adding {v_id}')
                route_latest_vls[v_id] = vls

        return

    def get_latest(self, route_tag : str):
        retval = []
        if route_tag not in self.latest_vls:
            return retval
        self.remove_stale_vlss(route_tag) # this could be slow, and really shouldn't be here
        route_map = self.latest_vls[route_tag]
        retval = route_map.values()
        return retval

    def remove_stale_vlss(self, route_tag:str):
        print(f'Removing stale vlss for {route_tag}')
        current_time: int = int(time.time())
        vlss = self.latest_vls[route_tag]
        for v_id in list(vlss):
            report_time = int(vlss[v_id].last_time / 1000)
            if current_time - report_time > 120:
                print(f'Removing {v_id} {current_time} {report_time} {current_time-report_time}')
                del vlss[v_id]
        print(f'Done removing stale vlss for {route_tag}')
        return

    def get_direction_by_tag(self, dirTag:str):
        direction = self.__direction_tag[dirTag]
        return direction

    def get_route_by_tag(self, routeTag:str):
        route = self.__routes[routeTag]
        return route

    def update_direction_vls(self, routeTag):
        new_latest_direction_vls = {}
        if routeTag not in self.latest_vls:
            return
        vlss: List[mm.VehicleLocationSnapshot] = self.latest_vls[routeTag].values()
        for vls in vlss:
            if vls.dirTag not in new_latest_direction_vls:
                new_latest_direction_vls[vls.dirTag] = []
            new_latest_direction_vls[vls.dirTag].append(vls)
        self.latest_direction_vls[routeTag] = new_latest_direction_vls


blob = DaBlob()
