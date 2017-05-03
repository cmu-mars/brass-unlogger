#!/usr/bin/python
import json
import glob
import sys
import os
import csv

# take directory of interest on the command line as the first argument.
target_dir = sys.argv[1]

for j_path in glob.glob('%s/*.json' % target_dir):
    ## skip the aggregated files; i don't know what they mean yet
    if 'aggregate' in j_path:
        continue

    basename = os.path.basename(j_path)

    ## split out the hash
    parts = basename.split('_')

    ## parts[2] ends in a '.json' because python basename isn't posix
    ## standard, so this grabs just the hash that they use to name each
    ## test.
    test_name = (parts[2].split('.'))[0]

    print test_name

    with open(j_path) as test_json:
        data = json.load(test_json)

        print (str(data))
