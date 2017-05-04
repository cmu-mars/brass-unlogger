#!/usr/bin/python
from __future__ import with_statement
import json
import glob
import sys
import os
import csv
import os.path
import re

from waypoints import WAYPOINTS

def get_map_coord(name):
    filtered = filter(lambda waypoint: waypoint["node-id"] == name, WAYPOINTS)
    if len(filtered) != 1:
        return {'x': "0.0", 'y' : "0,0"}
    wp = filtered[0]['coord']
    wp['x'] = str(wp['x'])
    wp['y'] = str(wp['y'])
    return wp

# find last location of robot

def get_log_entries(path):
    lines = []
    with open("%s/log" % path) as log:
        for line in log:
            lines.append(json.loads(line))
    return lines

def get_final_sim_time(path):
    lines = []
    with open("%s/results.json" % path) as log:
        lines = json.load(log)
    for i in lines:
        if "/action/done" in i["ENDPOINT"]:
            return int(i["ARGUMENTS"]["sim_time"])
    return 0

def get_final_location(path):
    end_time = get_final_sim_time(path)
    try:
        with open("%s/observe.log" % path) as obs:
            for line in obs:
                observation = json.loads(line)
                observation = observation["RESULT"]
                if end_time <= int(observation["sim_time"]):
                    observation["x"] = str(observation["x"])
                    observation["y"] = str(observation["y"])
                    return observation
    except IOError:
        return {"x" : "n/a", "y" : "n/a"}
    except TypeError:
        return {"x" : "n/a", "y" : "n/a"}
        
# Get the obstacle information from the log entries (test/log)
# Return empty array if it does not exist
def get_obstacle_information(log):
    info = {}
    remove_time_in_next_observe = False
    sim_time_pattern = re.compile('sim_time.: .(\d+)')

    for line in log:
        if "place_obstacle hit" in line["MESSAGE"]:
            message = line["MESSAGE"][len("/action/place_obstacle hit with "):]
            message = message.replace("u'", "'")
            message = message.replace("'", '"')
            loc = json.loads(message)
            info['x'] = str(loc["ARGUMENTS"]['x'])
            info['y'] = str(loc["ARGUMENTS"]['y'])
        elif "place_obstacle returning" in line["MESSAGE"]:
            message = line["MESSAGE"]
            m = sim_time_pattern.search(message)
            info['place_time'] = m.group(1)
        elif "remove_obstacle hit" in line["MESSAGE"]:
            remove_time_in_next_observe = True
        elif "observe returning" in line["MESSAGE"] and remove_time_in_next_observe:
            remove_time_in_next_observe = False
            m = sim_time_pattern.search(line["MESSAGE"])
            info['remove_time'] = m.group(1)
    print info
    return info

# take directory of interest on the command line as the first argument.
target_dir = sys.argv[1]

for j_path in glob.glob('%s/*.json' % target_dir):
    ## skip the aggregated files; i don't know what they mean yet
    if 'aggregate' in j_path:
        continue

    basename = os.path.basename(j_path)

    ## split out the hash
    json_parts = basename.split('_')

    ## parts[2] ends in a '.json' because python basename isn't posix
    ## standard, so this grabs just the hash that they use to name each
    ## test.
    test_name = (json_parts[2].split('.'))[0]

    with open(j_path) as test_json:
        test_data = json.load(test_json)

        for test_dir in glob.glob('%s/*%s*/' % (target_dir, test_name)):

            ## if valid, call bradley's with ('%s/test/' % test_dir)
            log_entries = get_log_entries('%s/test' % test_dir)
            final_location = get_final_location('%s/test' % test_dir)

            obstacle_information = get_obstacle_information(log_entries)
            
            test_dir_parts = test_dir.split("_")
            output = [
                ## cp level
                json_parts[0]

                ## case
                , test_dir_parts[2]

                ## json path
                , j_path

                ## data path
                , test_dir

                ## start name
                , test_data['configParams']['testInit']['start_loc']

                ## start x
                , get_map_coord(test_data['configParams']['testInit']['start_loc'])['x']

                ## start y
                , get_map_coord(test_data['configParams']['testInit']['start_loc'])['y']

                ## target name
                , test_data['configParams']['testInit']['target_loc']

                ## target x
                , get_map_coord(test_data['configParams']['testInit']['target_loc'])['x']

                ## target y
                , get_map_coord(test_data['configParams']['testInit']['target_loc'])['y']

                ## obstacle?
                , str(test_data['configParams']['testRun']['obsPert'])

                ## removed?
                , ('after %s' % test_data['configParams']['testRun']['obs_delay']) if test_data['configParams']['testRun']['obsPert'] else 'n/a'

                ## battery?
                , str(test_data['configParams']['testRun']['battPert'])

                ## kinect?
                , str(test_data['configParams']['testRun']['sensorPert'])

                ## outcome
                , test_data['test_outcome']

                ##Only cp1 has safety and timing, both have accuracy, and
                ##only cp2 has detection.

                ## gnarly index math going on here; could be wrong!

                ## accuracy
                , str(test_data[test_dir_parts[2]][0][1])

                ## timing -- if cp1
                , str(test_data[test_dir_parts[2]][1][1]) if json_parts[0] == "CP1" else "n/a"

                ## safety -- if cp1
                , str(test_data[test_dir_parts[2]][2][1]) if json_parts[0] == "CP1" else "n/a"

                ## detection -- if cp2
                , str(test_data[test_dir_parts[2]][1][1]) if json_parts[0] == "CP2" else "n/a"

                ## final x
                , final_location["x"]

                ## final y
                , final_location["y"]
                
                ## obstacle x, obstacle y, obstacle time, remove time, if there
                , obstacle_information['x'] if 'x' in obstacle_information else "n/a"
                , obstacle_information['y'] if 'y' in obstacle_information else "n/a"
                , obstacle_information['place_time'] if 'place_time' in obstacle_information else "n/a"
                , obstacle_information['remove_time'] if 'remove_time' in obstacle_information else "n/a"

                
            ]


            print (",").join(output)
