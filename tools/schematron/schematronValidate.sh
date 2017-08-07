#!/usr/bin/env bash
# Args: 1 - name of input file, 2 - name of output file (optional - defaults to file1-validate.xml)
# Exit code: 1 if validation error, 0 if none

if [ $# -lt 1 ]; then
	echo USAGE: "$0" infile OPTIONAL outfile
	exit 1
fi

infile=$1
if [[ $infile != /* ]]; then 
	# NOT an Absolute path - change relative path to be relateive to where script started
	infile=$PWD/$infile
fi

bashSourceDir=$(dirname "$0")

schematronScript=$bashSourceDir/codeListValidation.sch
saxonHome=$bashSourceDir/saxon
saxonJar=$saxonHome/saxon9he.jar
schematronHome=$bashSourceDir/schematron

if [ $# -eq 2 ]; then
	outfile=$2
else
	outfile=$infile-validate.xml
fi

# shellcheck disable=SC2154
if [ "$http_proxy" ]; then
    proxyHost=$(echo "$http_proxy" | sed 's/http[s]*:\/\///' | sed 's/:.*//')
    proxyPort=$(echo "$http_proxy" | sed 's/http[s]*:\/\///' | sed 's/.*://')
    javaFlags="-Dhttp.proxyHost=$proxyHost -Dhttp.proxyPort=$proxyPort -Dhttps.proxyHost=$proxyHost -Dhttps.proxyPort=$proxyPort"
fi

if [ -n "$JAVA_HOME" ]; then
    javaCmd="${JAVA_HOME}/bin/java"
else
    javaCmd="java"
fi

# Build the XSLT for the schematron
${javaCmd} "$javaFlags" \
		-jar "$saxonJar" \
		-s:"$schematronScript" \
		-xsl:"$schematronHome"/iso_svrl_for_xslt2_with_diagnostics.xsl \
		-o:"$schematronScript.xsl"

# Validate the input using the Schematron XSLT
${javaCmd} "$javaFlags" \
		-jar "$saxonJar" \
		-s:"$infile" -xsl:"$schematronScript.xsl" \
		-o:"$outfile"

# shellcheck disable=SC2034
failures=$(grep -i "failed-assert" "$outfile")

code=$?
# 0 is 'lines are selected' and 2 is 'some error'
if [ $code -eq 2 ] || [ $code -eq 0 ]; then
	echo Validate failed
	grep -i "failed-assert" "$outfile"
	exit 1
fi
