#!/bin/bash

if ! [ -e "results.csv" ]
then
    # turn header.csv into a csv instead of newline delimited, chopping off
    # the trailing comma from tr
   cat header.csv | tr '\n' ',' | sed 's/,$/\n/' >> results.csv

   for d in initialTests/*
   do
       ./unlogger.py $d >> results.csv
   done

#   ./unlogger.py randomTests/ >> results.csv
else
    echo "delete or cache the results file so it doesn't get clobbered"
fi
