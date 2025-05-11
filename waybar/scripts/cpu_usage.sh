#!/bin/bash

loadavg=$(cut -d " " -f1 /proc/loadavg)

cores=$(nproc)

usage=$(echo "$loadavg $cores" | awk '{ printf "%.0f", ($1 / $2) * 100 }')

echo "{\"text\": \"${usage}%\"}"