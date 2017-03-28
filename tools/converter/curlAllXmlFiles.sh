#!/usr/bin/env bash

for file in /home/heya/workspace/Geodesy-Web-Services/gws-system-test/src/test/resources/sitelogs/2017-03-27/geodesyml/*.xml
do
    curl --data-binary @${file} https://hdevgeodesy-webservices.geodesy.ga.gov.au/siteLogs/upload
done

