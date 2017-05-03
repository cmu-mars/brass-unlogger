#!/bin/bash

if ! [ -e "results.csv" ]
then
   cat header.csv >> results.csv

   for d in initialTests/*
   do
       ./unlogger.py $d >> results.csv
   done

   ./unlogger.py randomTests/ >> results.csv
else
    echo "delete or cache the results file so it doesn't get clobbered"
fi
