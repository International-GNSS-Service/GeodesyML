#!/usr/bin/env bash

# shellcheck source=/dev/null
. <(curl -s https://raw.githubusercontent.com/GeoscienceAustralia/trigger-travis/7c1b0f1d5abb02381805d8a4ccc467b1db5e6422/trigger-travis.sh)

declare -a downstream=("ogc-schemas")
trigger-travis "${downstream[@]}"

