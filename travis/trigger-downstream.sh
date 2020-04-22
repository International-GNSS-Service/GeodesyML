#!/usr/bin/env bash

# shellcheck source=/dev/null
. <(curl -s https://raw.githubusercontent.com/GeoscienceAustralia/trigger-travis/c1e157f8a648cbf90a18a75e29408af3bf9a3820/trigger-travis.sh)

declare -a downstream=("GeodesyML-Java-Bindings")
trigger-travis -b geodesyml-0.4 "${downstream[@]}"

