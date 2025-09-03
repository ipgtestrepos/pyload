#!/usr/bin/env bash

# Check if ipg exists
if ! command -v ipg &> /dev/null; then
    echo "Error: ipg is not PATH." >&2
    exit 1
fi

ipg auth company create --company spatz --legal-name "Spatz, Inc." --email info@spatz.com --url "http://www.spatz.com"

ipg prod import --company spatz --product mem_interface --release 1.0.0 \
	--source-root ./samp_metadata/product/spatzip/mem_interface

ipg prod import --company spatz --product reqrsp_interface --release 1.0.0 \
	--source-root ./samp_metadata/product/spatzip/reqrsp_interface

ipg prod import --company spatz --product snitch --release 1.0.0 \
	--source-root ./samp_metadata/product/spatzip/snitch

ipg prod import --company spatz --product spatz --release 1.0.0 \
	--source-root ./samp_metadata/product/spatzip/spatz

ipg prod import --company spatz --product tcdm_interface --release 1.0.0 \
	--source-root ./samp_metadata/product//spatziptcdm_interface

ipg prod import --company spatz --product sky130 --release 1.0.0 \
	--source-root ./samp_metadata/product/gds

