#!/usr/bin/python
from __future__ import with_statement
import json
import glob
import sys
import os
import csv

from waypoints import WAYPOINTS

def get_map_coord(name):
	global WAYPOINTS
	filtered = filter(lambda waypoint: waypoint["node-id"] == name, WAYPOINTS)
	if len(filtered) != 1:
		return {'x': "0.0", 'y' : "0,0"}
	wp = filtered[0]['coord']
	wp['x'] = str(wp['x'])
	wp['y'] = str(wp['y'])
	return wp

# find last location of robot
def get_final_sim_time(path):
	lines = []
	with open(path % "/test/results.json") as log:
		lines = json.load(log)
	
	
	for i in lines:
		if "/action/done" in i["ENDPOINT"]:
			return i["ARGUMENTS"]["sim_time"]
	return 0
	
def get_final_location(path):
	end_time = get_final_sim_time(path)
	with open(path % "/test/observe.log") as obs:
		for line in obs:
			observation = json.loads(line)
			if end_time <= observation["sim_time"]:
				observation["x"] = str(observation["x"])
				observation["y"] = str(observation["y"])
				return observation
	return {"x" : "0", "y" : "0"}		
		

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

    ## print test_name

    with open(j_path) as test_json:
        test_data = json.load(test_json)

        for test_dir in glob.glob('%s/*%s*/' % (target_dir, test_name)):

            ## if valid, call bradley's with ('%s/test/' % test_dir)

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
            ]


            print (",").join(output)
