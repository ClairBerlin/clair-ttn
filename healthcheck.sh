#!/bin/sh
MARKER_FILE="/tmp/clair-alive"
if [ -s $MARKER_FILE ]
then
    echo "Background thread was alive.";
    rm $MARKER_FILE
    exit 0
else
    echo "Background thread seems to be dead.";
    exit 1
fi
