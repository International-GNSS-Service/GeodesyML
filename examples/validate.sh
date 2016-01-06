#!/usr/bin/env bash

for example in *.xml; do
    ./xsd-validator/xsdv.sh ../schema/GeodesyML.xsd $example
    outcome+=$?
done

if (($outcome == 0)); then
    echo "OK, all examples successfully validated." && exit 0
else
    echo "Error, some examples failed to validate!" && exit -1
fi
