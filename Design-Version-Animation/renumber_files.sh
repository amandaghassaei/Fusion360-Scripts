#!/bin/bash
# To run:
# ./renumber_files.sh DIRECTORY_NAME

REORDER=1

find "$1" -name '*.png' | sort -V | while read f
do
	DEST=$(echo "$f" | sed 's/[0-9]*.png//g') #remove numbers and extension
	DEST="$DEST$REORDER.png"
        if [ "$DEST" != "$f" ]
        then
            mv "$f" "$DEST"
        fi
	((REORDER++))
done