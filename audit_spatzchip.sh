#!/usr/bin/env bash

# Check if ipg exists
if ! command -v ipg &> /dev/null; then
    echo "Error: ipg is not PATH." >&2
    exit 1
fi

cp -r samp_metadata/chip/spatz .
pushd spatz

ipg chip init --name spatz

ipg audit init --name audit1
ipg audit run audit1 --skip-errors --results



