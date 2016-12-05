#!/bin/sh
set -e


python -u collateontologies.py -o ncbitaxon -s 10000 &
python -u collateontologies.py -o efo &
wait

cat /data/tmp_ncbitaxon_terms.csv | head -n 1 > /data/ncbitaxon_terms.csv
cat /data/tmp_ncbitaxon_terms.csv | tail -n +2 | sort -u >> /data/ncbitaxon_terms.csv

cat /data/tmp_ncbitaxon_parents.csv | head -n 1 > /data/ncbitaxon_parents.csv
cat /data/tmp_ncbitaxon_parents.csv | tail -n +2 | sort -u >> /data/ncbitaxon_parents.csv



cat /data/tmp_efo_terms.csv | head -n 1 > /data/efo_terms.csv
cat /data/tmp_efo_terms.csv | tail -n +2 | sort -u >> /data/efo_terms.csv

cat /data/tmp_efo_parents.csv | head -n 1 > /data/efo_parents.csv
cat /data/tmp_efo_parents.csv | tail -n +2 | sort -u >> /data/efo_parents.csv




