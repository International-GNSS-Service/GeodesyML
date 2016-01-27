#!/usr/bin/env bash

cd $(dirname $0)

outcome=0

for example in *.xml; do
    ../tools/xsd-validator/xsdv.sh ../schema/geodesyML.xsd $example
    outcome+=$?
done

if [ $outcome -ne 0 ]; then
    echo "Error, some examples failed to validate!" && exit -1
fi

for example in *.xml; do
    FNAME=$(basename $example)
    ../tools/schematron/schematronValidate.sh $example /tmp/$FNAME.schematronvalidate.xml
    outcome+=$?
done

if [ $outcome -eq 0 ]; then
    echo "OK, all examples successfully validated." && exit 0
else
   echo "Error, some examples failed to schematron validate!" && exit -1
fi
