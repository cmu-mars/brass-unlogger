#!/usr/bin/python

import sys
import os
import csv
import svgwrite
import progressbar
from PIL import Image, ImageDraw

## read the results file into a list of dictionaries keyed on the header
## names.
try:
    with open('results.csv') as f:
        reader = csv.reader(f, skipinitialspace=True)
        header = next(reader)
        results = [dict(zip(header, row)) for row in reader]

except IOError:
    print "could not open results.csv"
    sys.exit(1)

try:
    os.mkdir('images')
except OSError:
    print "images directory already exists"
    sys.exit(1)

## start: green x
## target: green o
## final: yellow x
## obstacle: red box

bar = progressbar.ProgressBar()

for line in bar(results):
    mapbase = Image.open('Wean-entire-floor4.png')
    draw = ImageDraw.Draw(mapbase)

    draw.line((0, 0) + mapbase.size, fill=128)
    draw.line((0, mapbase.size[1], mapbase.size[0], 0), fill=128)
    del draw

    mapbase.save('images/%s.png' % os.path.basename(line['json path']).split('.')[0], "PNG")

    # line['start x']
    # line['start y']

    # line['target x']
    # line['target y']

    # line['final x']
    # line['final y']

    # line['obstacle x']
    # line['obstacle y']
