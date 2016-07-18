#!/bin/bash
#
# Generate GeodesyML documentation using OxygenML.  Requires this script be run a machine with a licensed copy of OxygenML
#
# Run from this directory since the input and output is relative

# Assuming running this on Mac (current status) - update for Linux or create a .bat version for Windows

SCRIPT=""
SCRIPTMAC=/Applications/oxygen/schemaDocumentationMac.sh
SCRIPTLINUX=/usr/local/bin/schemaDocumentation.sh
XSDDIR=../../schemas
XSDFILE=geodesyML
XSD=$XSDDIR/$XSDFILE.xsd
DOCFINALDIR=./doc
REPO="git@github.com:GeoscienceAustralia/GeodesyML.git master:gh-pages"
DATE=$(date +%Y-%m-%d)

if [[ -e $SCRIPTMAC ]]; then
    SCRIPT=$SCRIPTMAC
elif [[ -e $SCRIPTLINUX ]]; then
    SCRIPT=$SCRIPTLINUX
else
    echo schemaDocumentation.sh Mac or Linux does ot exist - $SCRIPTMAC or $SCRIPTLINUX
    exit 1
fi

if [[ ! -e $XSD ]]; then
    echo XSD doesnt exist: $XSD
    exit 1
fi

if [[ -d doc ]]; then 
    rm -rf doc
fi

echo $SCRIPT $XSD  -cfg:oxygen_17.1_generateDoco.settings

$SCRIPT $XSD  -cfg:oxygen_17.1_generateDoco.settings

if [[ $? -ne 0 ]]; then
    echo Error
    exit 1
fi

echo Schema doco generated to $XSDDIR.  Copy to $DOCFINALDIR and remove copy of .xsd files

cp -r $XSDDIR $DOCFINALDIR

rm -r $XSDDIR/img
rm $XSDDIR/*html
rm $XSDDIR/*css
 
cd $DOCFINALDIR
find . -name "*xsd" -exec rm {} \;

echo Git commit doco to $REPO

mv $XSDFILE.html index.html
git init
git add --all
git ci -m "Update oxygen generated schema documentation at $DATE"
git push --force $REPO

exit $?
