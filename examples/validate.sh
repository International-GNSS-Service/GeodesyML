#!/usr/bin/env bash

bashSourceDir=$(dirname "$0")
schemer=$bashSourceDir/../tools/xml-schemer/bin/schemer.sh
schematronValidate=$bashSourceDir/../tools/schematron/schematronValidate.sh

outcome=0

for example in ./*.xml; do
    # perform schema validation
    $schemer schema --catalog ../schemas/catalog.xml --xml "$example" --xsd ../schemas/geodesyML.xsd
    outcome+=$?

    # perform schematron validation
    $schematronValidate "$example" "/tmp/$(basename "$example").schematronvalidate.xml"
    outcome+=$?
done

if [ $outcome -ne 0 ]; then
    echo "Error, some examples failed to validate."
    exit 1
fi

echo "OK, all examples successfully validated."
