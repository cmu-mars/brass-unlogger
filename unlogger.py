#!/usr/bin/python
import json
import glob
import sys
import os

# take directory of interest on the command line as the first argument.
target_dir = sys.argv[1]

for j_path in glob.glob('%s/*.json' % target_dir):
    ## skip the aggregated files; i don't know what they mean yet
    if 'aggregate' in j_path:
        continue

    basename = os.path.basename(j_path)

    ## split out the hash
    parts = basename.split('_')
    test_name = (parts[2].split('.'))[0]

    print test_name

    with open(j_path) as f:
        data = json.load(f)
