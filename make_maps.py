#!/usr/bin/python

import sys
import os
import csv
import svgwrite

## read the results file into a list of dictionaries keyed on the header
## names.
try:
    with open('results.csv') as f:
        reader = csv.reader(f, skipinitialspace=True)
        header = next(reader)
        results = [dict(zip(header, row)) for row in reader]

except IOError:
    print "could not open results.csv"


## start: green x
## target: green o
## final: yellow x
## obstacle: red box

    # start x
    # start y
    # target x
    # target y
    # final x
    # final y
    # obstacle x
    # obstacle y

for line in results:
