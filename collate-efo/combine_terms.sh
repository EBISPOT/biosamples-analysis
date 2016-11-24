#!/usr/bin/env bash

origin=("${@: 1:$#-1}")
dest=${@: -1}

echo "Process started"
head -n 1 ${origin[0]} > ${dest}

echo "Combining files"
for f in ${origin[@]}
do
    tail -n +2 $f >> ${dest}
done

echo "Sorting results and save unique"
sort -u ${dest} > ${dest}
