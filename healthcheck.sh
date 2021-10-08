#!/bin/sh

# exit in case pidof exits with a non-zero status
set -e

PIDOF_PYTHON=`pidof python`
NROF_PYTHON_THREADS=`ls -1 /proc/$PIDOF_PYTHON/task | wc -l`

if [ "$NROF_PYTHON_THREADS" = 2 ]; then
    echo "Background thread was alive."
    exit 0
else
    echo "Background thread seems to be dead."
    exit 1
fi
