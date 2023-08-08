import json
import time
import mathy_module as mathy
import request_and_parsing_module as rpm


def output_direction_locations_json():
    route = "501"
    xml = rpm.request_route_config(route)
    (stops, directions) = rpm.extract_route_config(xml)
    stop = next(stop for stop in stops if stop.tag == "3399")
    print(f'{stop.title}')

    last_update_time = '0'
    delay = 20

    for i in range(100):
        xml = rpm.request_vehicle_locations(route, last_update_time)
        last_update_time, vehicle_location_snapshots = rpm.extract_vehicle_location_snapshots(xml)

        for vls in vehicle_location_snapshots:
            relative_position_to_stop = mathy.relative_position_to_stop(stop, directions, vls)
            #print(f'{vls.vehicle_id} {vls.dir_tag} {relative_position_to_stop}')
            state = None
            match relative_position_to_stop:
                case "before_stop_of_interest":
                    state = "before"
                case "after_stop_of_interest":
                    state = "after"
                case "vrd_unknown_stop_of_interest_may_be_on_vrd":
                    state = "unknown"
                case _:
                    continue

            report_time = int(vls.last_time / 1000) - vls.secs_since_report

            row = {}
            row['id'] = vls.vehicle_id
            row['time'] = report_time
            row['lat'] = vls.lat
            row['lng'] = vls.lon
            row['state'] = state
            row['dirTag'] = vls.dir_tag
            print(json.dumps(row))
        time.sleep(delay)


pass  # put break point so you can have console loaded
output_direction_locations_json()
