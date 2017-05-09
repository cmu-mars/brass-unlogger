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

## we use this string to mark cells as not applicable -- i.e. there's no
## final robot location because the test harness crashed
na = "n/a"

def get_map_coord(name):
    filtered = filter(lambda waypoint: waypoint["node-id"] == name, WAYPOINTS)
    if len(filtered) != 1:
        return {'x': "0.0", 'y' : "0,0"}
    wp = filtered[0]['coord']
    wp['x'] = float(wp['x'])
    wp['y'] = float(wp['y'])
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
    return -1

def get_final_location(path):
    end_time = get_final_sim_time(path)
    try:
        with open("%s/observe.log" % path) as obs:
            for line in obs:
                observation = json.loads(line)
                observation = observation["RESULT"]
                if end_time <= int(observation["sim_time"]):
                    observation["x"] = float(observation["x"])
                    observation["y"] = float(observation["y"])
                    observation["voltage"] = str(observation["voltage"])
                    return observation
    except IOError:
        return {"x" : na, "y" : na, "voltage" : na}
    except TypeError:
        return {"x" : na, "y" : na, "voltage" : na}

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
        elif "set_battery hit" in line["MESSAGE"]:
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
    return info

# take directory of interest on the command line as the first argument.
target_dir = sys.argv[1]

## functions per column, named as in header.csv
def cp_level():
    """which challenge problem, 1 or 2"""
    return json_parts[0]

def case():
    """which case, BaselineA = A, BaselineB = B, Challenge = C"""
    return test_dir_parts[2]

def start_name():
    """name of start waypoint"""
    return test_data['configParams']['testInit']['start_loc']

def start_x():
    """corresponding x of the start"""
    return get_map_coord(test_data['configParams']['testInit']['start_loc'])['x']

def start_y():
    """corresponding y of the start"""
    return get_map_coord(test_data['configParams']['testInit']['start_loc'])['y']

def target_name():
    """name of target waypoint"""
    return test_data['configParams']['testInit']['target_loc']

def target_x():
    """corresponding x of the target"""
    return target_location['x']

def target_y():
    """corresponding y of the target"""
    return target_location['y']

def obstacle():
    """was an obstacle placed?"""
    return test_data['configParams']['testRun']['obsPert']

def removed():
    """if an obstacle was placed, was it removed?"""
    if test_data['configParams']['testRun']['obsPert']:
        return test_data['configParams']['testRun']['obs_delay']
    return na

def battery_perturbed():
    """was the battery level changed?"""
    return test_data['configParams']['testRun']['battPert']

def batt_reduce():
    """if the battery level was changed, to what voltage?"""
    if 'voltage' in observations:
        return observations['voltage']
    return na

def batt_delay():
    """ if the battery level was changed, how long did they wait?"""
    return observations.get('battery_time', na)

def kinect():
    """ was the kinect bumped? """
    return test_data['configParams']['testRun']['sensorPert']

def kinect_delay():
    """ if the kinect was bumped, how long did they wait to bump it?"""
    return observations.get('kinect_time',na)

def outcome():
    """what was the overall outcome? invalid / valid?"""
    return test_data['test_outcome']

def accuracy():
    """the outcome of the accuracy intent"""
    return test_data[test_dir_parts[2]][0][1]

def timing():
    """the outcome of the timing intent, if in cp1"""
    if json_parts[0] == "CP1":
        return test_data[test_dir_parts[2]][1][1]
    return na

def safety():
    """the outcome of the safety intent, if in cp1"""
    if json_parts[0] == "CP1":
        return test_data[test_dir_parts[2]][2][1]
    return na

def detection():
    """the outcome of the detection intent, if in cp2"""
    if json_parts[0] == "CP2":
        return test_data[test_dir_parts[2]][1][1]
    return na

def final_x():
    """x coordinate of the robot when it ended"""
    return final_location["x"]

def final_y():
    """y coordinate of the robot when it ended"""
    return final_location["y"]

def final_voltage():
    """voltage of the robot when it ended"""
    return final_location["voltage"]

def distance_to_goal():
    """remaining distance between the final location and the goal location"""
    x1 , x2 , y1 , y2 = [target_location['x'],final_location['x'],
                         target_location['y'],final_location['y']]

    if na in [x1 , x2 , y1 , y2]:
        return na
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

def obstacle_x():
    """x of the obstacle (if placed)"""
    return observations.get('x', na)

def obstacle_y():
    """y of the obstacle (if placed)"""
    return observations.get('y', na)

def obstacle_time():
    """sim time of obstacle placement (if placed)"""
    return observations.get('place_time',na)

def removal_time():
    """sim time of obstacle removal (if placed and removed)"""
    return observations.get('remove_time',na)

def number_of_notifications():
    # count the number of lines in notifications.txt to count how
    # many times we send notifications
    try:
        if json_parts[0] == "CP1":
            num_notifications = 0
            with open('%s/test/mars_notifications.txt' % test_dir) as note_file:
                for l in note_file:
                    num_notifications += 1
            return num_notifications
        else:
            # there are only notifications in the CP1 condition
            return na
    # if the file isn't there, it's because there was an error condition
    # somewhere, so it's also not applicable
    except IOError:
        return na

def pert_detect_sim_time():
    """sim time when we noticed the perturbation"""
    return pert_simtime

def first_observed_sim_time():
    """the first sim time returned in any observe message (best estimate of start time)"""
    return first_simtime

def done_sim_time():
    """sim time when the challenge ended (e.g., report back that robot reached target)"""
    return done_simtime

def json_path():
    """path to json file describing this test"""
    return j_path

def data_path():
    """path to directory with logs for this test"""
    return test_dir


## read in the header file
with open('column-names.txt') as header_file:
    header_names = [elem.replace(' ', '_') for elem in header_file.read().splitlines()]

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
            target_location = get_map_coord(test_data['configParams']['testInit']['target_loc'])


            # read ll-api.log to compute the simtimes for when we
            # detect the perturbation and when we hit /action/done
            pert_simtime = na
            done_simtime = na

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
                pert_simtime = na
                done_simtime = na

            first_simtime = na
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
                first_simtime = na

            test_dir_parts = test_dir.split("_")

            print (",").join([str(locals()[name]()) for name in header_names])
