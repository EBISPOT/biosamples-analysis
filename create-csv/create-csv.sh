#!/bin/sh

python /create-csv.py

echo "Completed generating tmp files"

cat /data/tmp_attributes.csv | head -n 1 > /data/attributes.csv
cat /data/tmp_has_attribute.csv | head -n 1 > /data/has_attribute.csv
cat /data/tmp_has_iri.csv | head -n 1 > /data/has_iri.csv
cat /data/tmp_has_type.csv | head -n 1 > /data/has_type.csv
cat /data/tmp_has_value.csv | head -n 1 > /data/has_value.csv
cat /data/tmp_ontologies.csv | head -n 1 > /data/ontologies.csv
cat /data/tmp_samples.csv | head -n 1 > /data/samples.csv
cat /data/tmp_types.csv | head -n 1 > /data/types.csv
cat /data/tmp_values.csv | head -n 1 > /data/values.csv

cat /data/tmp_attributes.csv | tail -n +2 | sort -u >> /data/attributes.csv
cat /data/tmp_has_attribute.csv | tail -n +2 | sort -u >> /data/has_attribute.csv
cat /data/tmp_has_iri.csv | tail -n +2 | sort -u >> /data/has_iri.csv
cat /data/tmp_has_type.csv | tail -n +2 | sort -u >> /data/has_type.csv
cat /data/tmp_has_value.csv | tail -n +2 | sort -u >> /data/has_value.csv
cat /data/tmp_ontologies.csv | tail -n +2 | sort -u >> /data/ontologies.csv
cat /data/tmp_samples.csv | tail -n +2 | sort -u >> /data/samples.csv
cat /data/tmp_types.csv | tail -n +2 | sort -u >> /data/types.csv
cat /data/tmp_values.csv | tail -n +2 | sort -u >> /data/values.csv
