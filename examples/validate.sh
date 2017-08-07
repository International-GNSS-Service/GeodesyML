#!/usr/bin/env bash

bashSourceDir=$(dirname "$0")
schemer=$bashSourceDir/../tools/xml-schemer/bin/schemer.sh
schematronValidate=$bashSourceDir/../tools/schematron/schematronValidate.sh

outcome=0

for example in ./*.xml; do
    $schemer schema --catalog ../schemas/catalog.xml --xml "$example" --xsd ../schemas/geodesyML.xsd
    outcome+=$?
done

if [ $outcome -ne 0 ]; then
    echo "Error, some examples failed to validate!" && exit -1
fi

for example in ./*.xml; do
    FNAME=$(basename "$example")
    $schematronValidate "$example" "/tmp/$FNAME.schematronvalidate.xml"
    outcome+=$?
done

if [ $outcome -eq 0 ]; then
    echo "OK, all examples successfully validated." && exit 0
else
   echo "Error, some examples failed to schematron validate!" && exit -1
fi
