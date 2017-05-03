#!/bin/bash

cat header.csv >> results.csv

for d in initialTests/*
do
    unlogger.py d >> results.csv
done

unlogger.py randomTests/ >> results.csv
