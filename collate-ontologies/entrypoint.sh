#!/bin/sh
set -e

python -u collate-ontologies.py -o ncbitaxon -s 10000


cat /data/tmp_efo_terms.csv | head -n 1 > /data/efo_terms.csv
cat /data/tmp_efo_terms.csv | tail -n +2 | sort -u >> /data/efo_terms.csv

cat /data/tmp_efo_parents.csv | head -n 1 > /data/efo_parents.csv
cat /data/tmp_efo_parents.csv | tail -n +2 | sort -u >> /data/efo_parents.csv


