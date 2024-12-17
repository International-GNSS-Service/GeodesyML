#!/bin/bash

shopt -s nullglob

repositoryRoot=$(readlink -f "$(dirname "$0")/..")
schemer=$repositoryRoot/tools/xml-schemer/bin/schemer.sh
schematronValidate=$repositoryRoot/tools/schematron/schematronValidate.sh

versions=("0.4" "0.5" "0.6")

outcome=0


for version in "${versions[@]}"; do
  echo "Validating $version."
  for example in $repositoryRoot/examples/$version/*.xml; do
    echo "Validating $example."
    $schemer schema --catalog "$repositoryRoot"/schemas/catalog.xml --xml "$example" --xsd "$repositoryRoot"/schemas/geodesyml/"$version"/geodesyML.xsd
    outcome+=$?

    $schematronValidate "$example" "/tmp/$(basename "$example").schematronvalidate.xml"
    outcome+=$?
  done

done

if [ $outcome -ne 0 ]; then
    echo "Error, some examples failed to validate."
    exit 1
fi

echo "OK, all examples successfully validated."
