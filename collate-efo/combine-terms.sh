#!/usr/bin/env bash
echo "Process started"

origin=("${@: 1:$#-1}")
dest=${@: -1}
header=$(head -n 1 ${origin[0]})

echo "Combining files"
for f in ${origin[@]}
do
    tail -n +2 $f >> "tmp_file.csv"
done


echo "Sorting results and save unique"
echo $header > ${dest}
sort -u "tmp_file.csv" >> ${dest}

echo "Removing temp files"
rm -f "tmp_file.csv"
