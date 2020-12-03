#!/bin/bash

src_name=duska
dublf_path=../../DuBLF/dublf/
dupyf_path=../../../DuPYF/DuPYF/dupyf/

src_path=../$src_name/

# convert to absolute paths
duik_path=$(cd "$src_path"; pwd)
dublf_path=$(cd "$dublf_path"; pwd)
dupyf_path=$(cd "$dupyf_path"; pwd)


rm -r -f $src_name
mkdir $src_name

for file in $src_path/*.py; do
    cp -t $src_name "$file"
    echo "Deployed $file"
done

mkdir "$src_name/dublf"

for file in $dublf_path/*.py; do
    cp -t "$src_name/dublf" "$file"
    echo "Deployed DuBLF file $file"
done

for file in $dupyf_path/*.py; do
    cp -t "$src_name/dublf" "$file"
    echo "Deployed DuPYF file $file"
done

zip -r -m $src_name.zip $src_name

echo "Done!"