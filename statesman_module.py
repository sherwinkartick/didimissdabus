from typing import List

import models_module as mm
from models_module import VehicleLocationSnapshot


class DaBlob:
    __latest_vls = {}

    __routes = {}

    __direction_tag = {}

    def __init__(self):
        pass

    def add_route(self, route: mm.Route):
        self.__routes[route.tag] = route
        for _,direction in self.__direction_tag.items():
            if direction.route.tag == route.tag:
                del self.__direction_tag[route.tag]
        for direction in route.directions:
            self.__direction_tag[direction.tag] = direction

    def add_vls(self, vlss: List[mm.VehicleLocationSnapshot]):
        vls: VehicleLocationSnapshot
        for vls in vlss:
            route_tag = vls.routeTag
            v_id = vls.id
            dir_tag = vls.dirTag

            # dict.setdefault(key,[]).append(value), chaining is trouble though
            if route_tag not in self.__latest_vls:
                self.__latest_vls[route_tag] = {}

            route_map = self.__latest_vls[route_tag]
            if dir_tag is None:
                if v_id in route_map:
                    # print(f'deleting {v_id}')
                    del route_map[v_id]
            else:
                # if v_id not in route_map:
                #     print(f'adding {v_id}')
                route_map[v_id] = vls
        return

    def get_latest(self, route_tag : str):
        retval = []
        if route_tag not in self.__latest_vls:
            return retval
        route_map = self.__latest_vls[route_tag]
        retval = route_map.values()
        return retval

    def get_direction_by_tag(self, dirTag:str):
        direction = self.__direction_tag[dirTag]
        return direction

    def get_route_by_tag(self, routeTag:str):
        route = self.__routes[routeTag]
        return route


blob = DaBlob()
