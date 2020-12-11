#!/bin/bash

addons_path=~/.config/blender/2.91/scripts/addons

duska_path=../duska/
dublf_path=../../DuBLF/dublf/
dupyf_path=../../../DuPYF/DuPYF/dupyf/

# convert to absolute paths
duska_path=$(cd "$duska_path"; pwd)
dublf_path=$(cd "$dublf_path"; pwd)
dupyf_path=$(cd "$dupyf_path"; pwd)

rm -r -f "$addons_path/duska"
mkdir "$addons_path/duska"

for file in $duska_path/*.py; do
    ln -s -t "$addons_path/duska" "$file"
    echo "Linked $file"
done

mkdir "$addons_path/duska/dublf"

for file in $dublf_path/*.py; do
    ln -s -t "$addons_path/duska/dublf" "$file"
    echo "Linked DuBLF file $file"
done

for file in $dupyf_path/*.py; do
    ln -s -t "$addons_path/duska/dublf" "$file"
    echo "Linked DuPYF file $file"
done

echo "Done!"