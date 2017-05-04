#!/usr/bin/python
from __future__ import with_statement
import json
import glob
import sys
import os
import csv
import re
import math

from waypoints import WAYPOINTS

def dist(x1, y1, x2, y2):
    if "n/a" in [x1,x2,y1,y2]:
        return "n/a"
    return math.sqrt((float(x2) - float(x1))**2 + (float(y2) - float(y1))**2)

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
                    observation["voltage"] = str(observation["voltage"])
                    return observation
    except IOError:
        return {"x" : "n/a", "y" : "n/a", "voltage" : "n/a"}
    except TypeError:
        return {"x" : "n/a", "y" : "n/a", "voltage" : "n/a"}

# Get the obstacle information from the log entries (test/log)
# Return empty array if it does not exist
def get_observations(log):
    info = {}
    remove_time_in_next_observe = False
    battery_time_in_next_observe = False
    kinect_time_in_next_observe = False

    def process_next_observe():
        return remove_time_in_next_observe or battery_time_in_next_observe or kinect_time_in_next_observe;

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
        elif "set_voltage hit" in line["MESSAGE"]:
            message = line["MESSAGE"][len("/action/set_voltage hit with "):]
            message = message.replace("u'", "'")
            message = message.replace("'", '"')
            loc = json.loads(message)
            info['voltage'] = str(loc["ARGUMENTS"]['voltage'])
            battery_time_in_next_observe = True
        elif "perturb_sensor hit" in line["MESSAGE"]:
            kinect_time_in_next_observe = True;
        elif "observe returning" in line["MESSAGE"] and process_next_observe():
            m = sim_time_pattern.search(line["MESSAGE"])
            if remove_time_in_next_observe:
                remove_time_in_next_observe = False
                info['remove_time'] = m.group(1)
            if battery_time_in_next_observe:
                battery_time_in_next_observe = False
                info['battery_time'] = m.group(1)
            if kinect_time_in_next_observe:
                kinect_time_in_next_observe = False
                info['kinect_time'] = m.group(1)

    ## print info ## any printing to std out breaks the csv because we make
            ## it just by shell redirects
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

            observations = get_observations(log_entries)

            # store the target x and y coordinates, because we use them
            # several times below
            target_x = get_map_coord(test_data['configParams']['testInit']['target_loc'])['x']
            target_y = get_map_coord(test_data['configParams']['testInit']['target_loc'])['y']

            # count the number of lines in notifications.txt to count how
            # many times we send notifications
            num_notifications = "n/a"
            try:
                if json_parts[0] == "CP1":
                    num_notifications = 0
                    with open('%s/test/mars_notifications.txt' % test_dir) as note_file:
                        for l in note_file:
                            num_notifications += 1
            except IOError:
                num_notifications = "n/a"

            # read ll-api.log to compute the simtimes for when we
            # detect the perturbation and when we hit /action/done
            pert_simtime = "n/a"
            done_simtime = "n/a"

            done_time_hit = False
            try:
                with open('%s/test/ll-api.log' % test_dir) as api_file:
                    for line in api_file:
                        if "PERTURBATION_DETECTED" in line:
                            data = json.loads(((":").join((line.split(':'))[1:])))
                            pert_simtime = str(data['MESSAGE']['sim_time'])

                        # we may hit done many times, or none at all. this
                        # will record the first, leaving the values as n/a
                        # if there are none (i.e. because we hit time out
                        # and never notified)
                        if (not done_time_hit) and ("/action/done" in line):
                            done_time = True
                            data = json.loads(((":").join((line.split(':'))[1:])))
                            done_simtime = str(data['ARGUMENTS']['sim_time'])
            except IOError:
                pert_simtime = "n/a"
                done_simtime = "n/a"

            first_simtime = "n/a"
            # find the sim time in the first time they hit our
            # observe. this is somewhat redundant to the get_observations
            # above, but since it only looks at a prefix of the file, it's
            # faster and fine for now.
            try:
                with open('%s/test/log' % test_dir) as log_file:
                    for line in log_file:
                        if "/action/observe returning response" in line:
                            ## easier to grab it with a regex as above,
                            ## because it's in escaped json in a string
                            sim_time_pattern = re.compile('sim_time..: ..(\d+)')
                            m = sim_time_pattern.search(line)
                            first_simtime = m.group(1)
                            break
            except IOError:
                first_simtime = "n/a"

            test_dir_parts = test_dir.split("_")
            output = [
                ## cp level
                json_parts[0]

                ## case
                , test_dir_parts[2]

                ## start name
                , test_data['configParams']['testInit']['start_loc']

                ## start x
                , get_map_coord(test_data['configParams']['testInit']['start_loc'])['x']

                ## start y
                , get_map_coord(test_data['configParams']['testInit']['start_loc'])['y']

                ## target name
                , test_data['configParams']['testInit']['target_loc']

                ## target x
                , target_x

                ## target y
                , target_y

                ## obstacle?
                , str(test_data['configParams']['testRun']['obsPert'])

                ## removed?
                , str(test_data['configParams']['testRun']['obs_delay']) if test_data['configParams']['testRun']['obsPert'] else 'n/a'

                ## battery?
                , str(test_data['configParams']['testRun']['battPert'])

                ## perturb level battery level
                , observations['voltage'] if 'voltage' in observations else "n/a"
                #, str(test_data['configParams']['testRun']['batt_reduce']) if test_data['configParams']['testRun']['battPert'] else "n/a"

                ## time perturbed
                , observations['battery_time'] if 'battery_time' in observations else "n/a"
                #, str(test_data['configParams']['testRun']['batt_delay']) if test_data['configParams']['testRun']['battPert'] else "n/a"

                ## kinect?
                , str(test_data['configParams']['testRun']['sensorPert'])

                ## kinect delay
                , observations['kinect_time'] if 'kinect_time' in observations else "n/a"
                #, str(test_data['configParams']['testRun']['bump_delay']) if test_data['configParams']['testRun']['sensorPert'] else "n/a"

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

                ## final voltage
                , final_location["voltage"]

                ## distance from goal
                , str(dist(target_x,target_y,final_location["x"],final_location["y"]))

                ## obstacle x, obstacle y, obstacle time, remove time, if there
                , observations['x'] if 'x' in observations else "n/a"
                , observations['y'] if 'y' in observations else "n/a"
                , observations['place_time'] if 'place_time' in observations else "n/a"
                , observations['remove_time'] if 'remove_time' in observations else "n/a"

                # notifications
                , str(num_notifications)

                # sim time that the perturbation was detected
                , pert_simtime

                # first observed sim time
                , first_simtime

                # sim time when the challenge ended
                , done_simtime

                ## json path
                , j_path

                ## data path
                , test_dir
            ]

            print (",").join(output)
