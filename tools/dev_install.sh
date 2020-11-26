#!/bin/bash

addons_path=~/.config/blender/2.91/scripts/addons

duska_path=../duska/
dublf_path=../../DuBLF/dublf/
dupyf_path=../../../DuPYF/DuPYF/dupyf/

duska_path=$(cd "$duska_path"; pwd)
dublf_path=$(cd "$dublf_path"; pwd)
dupyf_path=$(cd "$dupyf_path"; pwd)

rm -r -f "$addons_path/duska"
mkdir "$addons_path/duska"

for file in $duska_path/*.py; do
    ln -s -t "$addons_path/duska" "$file"
    echo "Linked $file"
done

ln -s -t "$addons_path/duska" "$dublf_path"
echo "Linked DuBLF"
ln -s -t "$addons_path/duska" "$dupyf_path"
echo "Linked DuPYF"
echo "Done!"