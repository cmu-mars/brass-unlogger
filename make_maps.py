#!/usr/bin/python

import sys
import os
import csv
import svgwrite
import progressbar
from PIL import Image, ImageDraw, ImageFont

## read the results into a list of dictionaries keyed by the headers
try:
    with open('results.csv') as f:
        reader = csv.reader(f, skipinitialspace=True)
        header = next(reader)
        results = [dict(zip(header, row)) for row in reader]
except IOError:
    print "could not open results.csv"
    sys.exit(1)

## make a directory to put the images, or bail if it exits already
try:
    os.mkdir('images')
except OSError:
    print "images directory already exists"
    sys.exit(1)

def trans(x,y,imgw,imgh):
    """translate coordinates from the json axes to the image"""
    return (float(x)/0.054, imgh - float(y)/0.054)

## for each dictionary (i.e. row of the CSV) do the drawing you want. we
## add a progress bar because it takes a little while.
fnt = ImageFont.truetype('hockey.ttf', 40)
na = "n/a"
bar = progressbar.ProgressBar(widgets=[progressbar.Bar(),' (', progressbar.ETA(), ') ',])

for line in bar(results):
    mapbase = Image.open('Wean-entire-floor4.png')
    draw = ImageDraw.Draw(mapbase)
    width, height = mapbase.size

    if line['start x'] != na and line['start y'] != na:
        # green 0,128,0
        x,y = trans(line['start x'], line['start y'], width, height)
        draw.ellipse((x - 5, y-5, x+5, y+5), fill='black', outline='black')
        draw.text((x,y),
                  "start",
                  font=fnt,
                  fill=(0,128,0,255))

    if line['target x'] != na and line['target y'] != na:
        # orange 255,165,0
        x,y = trans(line['target x'],line['target y'], width, height)
        draw.ellipse((x - 5, y-5, x+5, y+5), fill='black', outline='black')

        draw.text((x,y),
                  "target",
                  font=fnt,
                  fill=(255,165,0,255))

    if line['final x'] != na and line['final y'] != na:
        # yellow 255,255,0
        x,y = trans(line['final x'],line['final y'], width, height)
        draw.ellipse((x - 5, y-5, x+5, y+5), fill='black', outline='black')

        draw.text((x,y),
                  "final",
                  font=fnt,
                  fill=(127,127,0,255))

    if line['obstacle x'] != na and line['obstacle y'] != na:
        # red 255,0,0
        x,y = trans(line['obstacle x'],line['obstacle y'], width, height)
        draw.rectangle((x-1/0.054,y-1/0.054,x+1/0.054,y+1/0.054), fill=(200,0,0,255), outline=(200,0,0,255))
        draw.text((x,y),
                  "obstacle",
                  font=fnt,
                  fill=(200,0,0,255))

    del draw

    mapbase.save('images/%s-%s.png' %
                 (os.path.basename(line['json path']).split('.')[0],
                  line['case']),
                 "PNG")
