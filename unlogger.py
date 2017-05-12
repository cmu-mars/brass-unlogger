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
        return {'x': "0.0", 'y' : "0.0"}
    wp = filtered[0]['coord']
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
                    # todo: i don't know why these lines are needed
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
    action_error_patterb = re.compile('action/(.*) raised an exception')
    start_returned = False
    for line in log:
        if "place_obstacle hit" in line["MESSAGE"]:
            message = line["MESSAGE"][len("/action/place_obstacle hit with "):]
            message = message.replace("u'", "'")
            message = message.replace("'", '"')
            loc = json.loads(message)
            info['x'] = str(loc["ARGUMENTS"]['x'])
            info['y'] = str(loc["ARGUMENTS"]['y'])
        elif "start returning" in line["MESSAGE"]:
            start_returned = True
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
        elif "rainbow failed to start" in line["MESSAGE"]:
            info['rainbow_error'] = True
        elif "has same start and end locations" in line["MESSAGE"]:
            info['config_same_start_end'] = True
        elif action_error_patterb.search(line["MESSAGE"]):
            info['endpoint_error'] = action_error_patterb.search(line["MESSAGE"]).group(1)
        elif "couldn't connect to TH" in line["MESSAGE"]:
            info['TH_error'] = True
        elif "posting status TEST_ERROR" in line["MESSAGE"]:
            info['TEST_ERROR'] = line["MESSAGE"]
    info['start_returned'] = start_returned
    return info

def process_start_log(path):
    start_info = {}
    try:
        gzpattern = re.compile("process has died.*gzserver")
        #rbwpattern = re.compile("rainbow failed to start")
        with open("%s/start.sh.log" % path) as start:
            for line in start:
                if (gzpattern.search(line)):
                    start_info["gazebo_error"] = "GAZ"
                    return start_info
                elif "Header is empty" in line:
                    start_info["gazebo_error"] = "GAZM"
                    return start_info
                elif re.search('gzserver.*boost.*failed', line):
                    start_info["gazebo_error"] = "GAZB";
                    return start_info
                elif "TF_NAN_INPUT" in line:
                    start_info["gazebo_error"] = "NaN";
                    return start_info;
        return start_info
        # with open("%s/log" %path) as log:
            # for line in log:
                # if (rbwpattern.search(line)):
                    # return "RBW"
        # return ""
    except IOError:
        return start_info
    except TypeError:
        return start_info

def process_rainbow_log(path):
    rainbow_info = {"delta_err" : 0, "ground_err" : 0, "plans_executed" : 0, "adaptations" : 0, "failed_adaptations" : 0}
    try:
        with open('%s/rainbow.log' %path) as rainbow:
            for line in rainbow:
                if "Calibration error detected by delta" in line:
                    rainbow_info["delta_err"] = rainbow_info["delta_err"] + 1
                elif "Calibration error detected by ground" in line:
                    rainbow_info["ground_err"] = rainbow_info["ground_err"] + 1
                elif "Got a new plan -- executing" in line:
                    rainbow_info["plans_executed"] = rainbow_info["plans_executed"] + 1
                elif "Found new plan" in line:
                    rainbow_info["adaptations"] = rainbow_info["adaptations"] + 1
                elif "Generating last resort plan" in line:
                    rainbow_info["failed_adaptations"] = rainbow_info["failed_adaptations"] + 1

    except IOError:
        return rainbow_info
    except TypeError:
        return rainbow_info

    return rainbow_info

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
    l = [target_location['x'],final_location['x'],
         target_location['y'],final_location['y']]

    if na in l:
        return na

    x1 , x2 , y1 , y2 = l
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
    try:
        # this is probably somewhat redundant to the get_observations above
        with open('%s/test/ll-api.log' % test_dir) as api_file:
            for line in api_file:
                if "PERTURBATION_DETECTED" in line:
                    data = json.loads(((":").join((line.split(':'))[1:])))
                    return data['MESSAGE']['sim_time']
        return na
    except IOError:
        return na

def first_observed_sim_time():
    """the first sim time returned in any observe message (best estimate of start time)"""
    # this is probably somewhat redundant to the get_observations above
    try:
        sim_time_pattern = re.compile('sim_time..: ..(\d+)')
        with open('%s/test/log' % test_dir) as log_file:
            for line in log_file:
                if "/action/observe returning response" in line:
                    # todo; what if it doesn't match
                    m = sim_time_pattern.search(line)
                    return m.group(1)
        return na
    except IOError:
        return na

def done_sim_time():
    """sim time when the challenge ended (e.g., report back that robot reached
       target). we may have sent the done message multiple times; this reports the
       first"""
    try:
        ## todo: this may be redundant with some of the other log scraping
        with open('%s/test/ll-api.log' % test_dir) as api_file:
            for line in api_file:
                if "/action/done" in line:
                    data = json.loads(((":").join((line.split(':'))[1:])))
                    return data['ARGUMENTS']['sim_time']
        return na
    except IOError:
        return na

def json_path():
    """path to json file describing this test"""
    return j_path

def data_path():
    """path to directory with logs for this test"""
    return test_dir

def failure_reason():
    """return the reason for an error, if it is there"""
    if "rainbow_error" in observations:
        return "RBW"
    if "gazebo_error" in start_info:
        return start_info["gazebo_error"]
    if "config_same_start_end" in observations:
        return "CSE"
    if "endpoint_error" in observations:
        return 'EPE %s' % observations['endpoint_error']
    if "TH_error" in observations:
        return "TH"
    if "TEST_ERROR" in observations:
        return "TE %s" % observations["TEST_ERROR"]
    if not observations['start_returned']:
        return "STF"
    return na

def bump_delta():
    """return the number of times in a test delta error caught miscalibration"""
    return rainbow_info["delta_err"]

def bump_ground():
    """return the number of times in a test ground error caught miscalibration"""
    return rainbow_info["ground_err"]

def plans_issued():
    """return the number of times in a test that rainbow issued a new plan"""
    return rainbow_info["plans_executed"]

def adaptations_tried():
    """return the number of times rainbow tried to find a plan"""
    return rainbow_info["adaptations"]

def adaptations_failed():
    """returns the number of times rainbow couldn't find a plan"""
    return rainbow_info["failed_adaptations"]


## read in the column name file
with open('column-names.txt') as header_file:
    header_names = [elem.replace(' ', '_') for elem in header_file.read().splitlines()]

for j_path in glob.glob('%s/*.json' % target_dir):
    ## skip the aggregated files
    if 'aggregate' in j_path:
        continue

    ## split the file name on underscores
    json_parts = os.path.basename(j_path).split('_')

    ## parts[2] ends in a '.json' because python basename isn't posix
    ## standard, so this grabs just the hash that they use to name each
    ## test.
    test_name = (json_parts[2].split('.'))[0]

    with open(j_path) as test_json:
        test_data = json.load(test_json)

        for test_dir in glob.glob('%s/*%s*/' % (target_dir, test_name)):
            # collect data used by more than one column below.
            log_entries = get_log_entries('%s/test' % test_dir)
            final_location = get_final_location('%s/test' % test_dir)
            observations = get_observations(log_entries)
            target_location = get_map_coord(test_data['configParams']['testInit']['target_loc'])
            start_info = process_start_log("%s/test" %test_dir)
            rainbow_info = process_rainbow_log('%s/test' %test_dir)


            test_dir_parts = test_dir.split("_")

            print (",").join([str(locals()[name]()) for name in header_names])
