#!/usr/bin/env bash

cd $(dirname $0)

for example in *.xml; do
    ./xsd-validator/xsdv.sh ../schema/geodesyML.xsd $example
    outcome+=$?
done

if [ $outcome -eq 0 ]; then
    echo "OK, all examples successfully validated." && exit 0
else
    echo "Error, some examples failed to validate!" && exit -1
fi
