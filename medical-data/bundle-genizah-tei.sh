#!/usr/bin/env bash
#set -Eeuxo pipefail

read -r -d '' USAGE << EOF
usage: bundle-genizah-tei.sh <cudl-data-dir> <dest>
Extract just Genizah TEI documents from a CUDL data repo.
EOF

if [ "$#" -ne 2 ]; then
    echo "$USAGE" 2>&1
    exit 1
fi

DEST="$(realpath "$2")"

cd "$1/data/tei" && grep --recursive --files-with-matches --null --fixed-strings 'http://id.loc.gov/authorities/subjects/sh85018717.html' . \
    | tar --null --files-from - --use-compress-program 'lzma --best' -cf "$DEST"
