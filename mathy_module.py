import pyproj


def before_stop(stop_of_interest, stops, vehicle_location_snapshot):
    v = vehicle_location_snapshot
    v_lat = v.lat
    v_lon = v.lon
    stop_index = stops.index(stop_of_interest)
    closest_stop_pair = None
    for stop_from, stop_to in zip(stops[::1], stops[1::1]):
        inbetween = triangle_inequality(v_lat, v_lon, stop_from.lat, stop_from.lon, stop_to.lat, stop_to.lon)

        if closest_stop_pair is not None:
            if inbetween < closest_stop_pair["inbetween"]:
                closest_stop_pair = {"vehicle_location_snapshot": vehicle_location_snapshot, "stop_from": stop_from,
                                     "stop_to": stop_to, "inbetween": inbetween}
        else:
            closest_stop_pair = {"vehicle_location_snapshot": vehicle_location_snapshot, "stop_from": stop_from,
                                 "stop_to": stop_to, "inbetween": inbetween}
    stop_to_index = stops.index(closest_stop_pair["stop_to"])
    return stop_to_index <= stop_index


def triangle_inequality(v_lat, v_lon, stop_from_lat, stop_from_lon, stop_to_lat, stop_to_lon):
    geodesic = pyproj.Geod(ellps='WGS84')
    _, _, distance_vehicle_from = geodesic.inv(stop_from_lon, stop_from_lat, v_lon, v_lat)
    _, _, distance_vehicle_to = geodesic.inv(stop_to_lon, stop_to_lat, v_lon, v_lat)
    _, _, distance_to_from = geodesic.inv(stop_from_lon, stop_from_lat, stop_to_lon, stop_to_lat)
    inbetween = abs(distance_to_from - (distance_vehicle_from + distance_vehicle_to))
    return inbetween


# hackiness
def guess_if_stop_in_direction_tag(stop, direction_tag):
    retval = False
    if stop.tag == "3399" and direction_tag.startswith("501_0"):
        retval = True
    return retval


def relative_position_to_stop(stop_of_interest, directions, vehicle):
    retval = "vehicle_missing_route_direction"
    if vehicle.dir_tag is not None:
        direction_found_bool = any(direction.tag == vehicle.dir_tag for direction in directions)
        if direction_found_bool:
            v_direction = next(direction for direction in directions if direction.tag == vehicle.dir_tag)
            v_stops = v_direction.route_stops
            if stop_of_interest in v_stops:
                before = before_stop(stop_of_interest, v_stops, vehicle)
                if before:
                    retval = "before_stop_of_interest"
                else:
                    retval = "after_stop_of_interest"
            else:
                retval = "stop_of_interest_not_on_vehicle_route_direction"
        else:
            in_direction = guess_if_stop_in_direction_tag(stop_of_interest, vehicle.dir_tag)
            if in_direction:
                retval = "vrd_unknown_stop_of_interest_may_be_on_vrd"
            else:
                retval = "vehicle_route_direction_unknown"

    return retval
