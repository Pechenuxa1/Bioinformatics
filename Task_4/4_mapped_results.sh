#!/bin/bash

FLAGSTAT_FILE=$1

MAPPED=$(grep -m 1 "mapped (" $FLAGSTAT_FILE | awk '{print $5}' | sed 's/[(%]//g')

echo "Mapped: $MAPPED%"
