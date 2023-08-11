import models_module as mm


class DaBlob:
    __all_vls = {}

    def __init__(self):
        pass

    def add_vls(self, vls: mm.VehicleLocationSnapshot):
        #print(f'{vls.vehicle_id} {vls.last_time}')
        route = vls.route_tag
        v_id = vls.vehicle_id
        dir_tag = vls.dir_tag

        # dict.setdefault(key,[]).append(value), chaining is trouble though
        if route not in self.__all_vls:
            self.__all_vls[route] = {}

        route_map = self.__all_vls[route]
        if dir_tag is None:
            if v_id in route_map:
                #print(f'deleting {v_id}')
                del route_map[v_id]
        else :
            # if v_id not in route_map:
            #     print(f'adding {v_id}')
            route_map[v_id] = vls
        return

    def get_latest(self, route):
        retval = []
        if route not in self.__all_vls:
            return retval
        route_map = self.__all_vls[route]
        retval = route_map.values()
        return retval


blob = DaBlob()
