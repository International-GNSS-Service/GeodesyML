#!/usr/bin/env bash

shopt -s nullglob

bashSourceDir=$(dirname "$0")
schemer=$bashSourceDir/../tools/xml-schemer/bin/schemer.sh
schematronValidate=$bashSourceDir/../tools/schematron/schematronValidate.sh

versions=("0.4")

outcome=0

for version in "${versions[@]}"; do
    for example in ./$version/*.xml; do
        echo "Validating $example."

        # perform schema validation
        $schemer schema --catalog ../schemas/catalog.xml --xml "$example" --xsd ../schemas/geodesyml/"$version"/geodesyML.xsd
        outcome+=$?

        # perform schematron validation
        $schematronValidate "$example" "/tmp/$(basename "$example").schematronvalidate.xml"
        outcome+=$?
    done
done

if [ $outcome -ne 0 ]; then
    echo "Error, some examples failed to validate."
    exit 1
fi

echo "OK, all examples successfully validated."
