#!/usr/bin/env bash
set -e

FILE=mktemp
pipenv run pip freeze | grep -vP '^genizah-data-tools==' > "$FILE"
printf '\n./genizah-tools\n' >> "$FILE"

mv "$FILE" binder/requirements.txt
