#!/usr/bin/env bash

cat args.txt | \
  awk '{ print "app.py --file=file.csv --offset="$1" --size="$2}' | \
  xargs -n 4 -P 8 python | \
  gawk ' { a+=1; b+=1000; c+=$1; printf("Done: %d; Found: %d; SubTotal: %d; Processed: %d\n", a,$1, c,b) } END { printf("\nTotal HIGH: %s; Total Attributes: %s; Ratio: %.2f%", c,b, 100*c/b)}'
