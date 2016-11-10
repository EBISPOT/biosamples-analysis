(cat sample_header.csv && (cat ../biosamples-annotations-1.csv | tail -n +2 | cut -d, -f1)) > ../output/sample.csv
