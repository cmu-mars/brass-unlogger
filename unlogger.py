#!/usr/bin/python
from __future__ import with_statement
import json
import glob
import sys
import os
import csv

WAYPOINTS = [
        {
            "connected-to": [
                "l2"
            ],
            "coord": {
                "x": 14.8,
                "y": 69
            },
            "node-id": "l1"
        },
        {
            "connected-to": [
                "l1",
                "c1",
                "c2"
            ],
            "coord": {
                "x": 19.8,
                "y": 69
            },
            "node-id": "l2"
        },
        {
            "connected-to": [
                "c2",
                "c3",
                "l4"
            ],
            "coord": {
                "x": 42.5,
                "y": 69
            },
            "node-id": "l3"
        },
        {
            "connected-to": [
                "l3",
                "ls",
                "l5"
            ],
            "coord": {
                "x": 52.2,
                "y": 69
            },
            "node-id": "l4"
        },
        {
            "connected-to": [
                "l4",
                "l6"
            ],
            "coord": {
                "x": 52.2,
                "y": 58.8
            },
            "node-id": "l5"
        },
        {
            "connected-to": [
                "l5",
                "c3",
                "c4"
            ],
            "coord": {
                "x": 42.5,
                "y": 58.8
            },
            "node-id": "l6"
        },
        {
            "connected-to": [
                "c4",
                "c1"
            ],
            "coord": {
                "x": 19.8,
                "y": 58.8
            },
            "node-id": "l7"
        },
        {
            "connected-to": [
                "l4"
            ],
            "coord": {
                "x": 52.2,
                "y": 74.4
            },
            "node-id": "ls"
        },
        {
            "connected-to": [
                "l2",
                "l7"
            ],
            "coord": {
                "x": 19.8,
                "y": 65
            },
            "node-id": "c1"
        },
        {
            "connected-to": [
                "l2",
                "l3"
            ],
            "coord": {
                "x": 31.1,
                "y": 69
            },
            "node-id": "c2"
        },
        {
            "connected-to": [
                "l3",
                "l6"
            ],
            "coord": {
                "x": 42.5,
                "y": 65
            },
            "node-id": "c3"
        },
        {
            "connected-to": [
                "l6",
                "l7"
            ],
            "coord": {
                "x": 31.1,
                "y": 58.8
            },
            "node-id": "c4"
        }
    ]

def get_map_coord(name):
	global WAYPOINTS
	filtered = filter(lambda waypoint: waypoint["node-id"] == name, WAYPOINTS)
	if len(filtered) != 1:
		return {'x': "0.0", 'y' : "0,0"}
	wp = filtered[0]['coord']
	wp['x'] = str(wp['x'])
	wp['y'] = str(wp['y'])
	return wp


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
                , ('after %s' % test_data['configParams']['testRun']['obs_dlay']) if test_data['configParams']['testRun']['obsPert'] == 'true' else 'n/a'

                ## battery?

                ## kinect?

                ## outcome
            ]


            print (",").join(output)
