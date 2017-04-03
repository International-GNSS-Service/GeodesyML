#!/usr/bin/env python
# Script to create a gco:codeList from an input file with a list of countries such as 
# https://raw.githubusercontent.com/lukes/ISO-3166-Countries-with-Regional-Codes/master/all/all.xml
# (https://github.com/lukes/ISO-3166-Countries-with-Regional-Codes),

import xml.etree.ElementTree as ET
import datetime
import random

inputFile="country-codes-source.xml"
outputFile="country-codes-codelist.xml"
theDate=datetime.date.today()

tree = ET.parse(inputFile)


def writeHeader(file):
    header=("<CT_CodelistCatalogue xmlns='http://www.isotc211.org/2005/gmx' \n"
"               xmlns:gco='http://www.isotc211.org/2005/gco' xmlns:gml='http://www.opengis.net/gml/3.2' \n"
"               xmlns:xlink='http://www.w3.org/1999/xlink' xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance'>\n"
"    <name>\n"
"        <gco:CharacterString>GeodesyML Country Codes</gco:CharacterString>\n"
"    </name>\n"
"    <scope>\n"
"        <gco:CharacterString>eGeodesy</gco:CharacterString>\n"
"    </scope>\n"
"    <fieldOfApplication>\n"
"        <gco:CharacterString>Geodesy</gco:CharacterString>\n"
"    </fieldOfApplication>\n"
"    <versionNumber>\n"
"        <gco:CharacterString>0.3</gco:CharacterString>\n"
"    </versionNumber>\n"
"    <versionDate>\n"
"        <gco:Date>"+theDate.strftime('%d-%m-%Y')+"</gco:Date>\n"
"    </versionDate>\n"
"    <codelistItem>\n"
"        <CodeListDictionary gml:id='GeodesyML_CountryCode'>\n"
"            <gml:description>GeodesyML Country Codes</gml:description>\n"
"            <gml:identifier codeSpace='urn:xml-gov-au:icsm:egeodesy:0.4'>GeodesyML_CountryCode</gml:identifier>\n")
    file.write(header)

def writeFooter(file):
    footer=("        </CodeListDictionary>\n"
"    </codelistItem>\n"
"</CT_CodelistCatalogue>\n")
    file.write(footer)

def buildAlpha(elem):
    alpha=''
    if (elem.get('alpha-3')):
        alpha = elem.get('alpha-3')
    elif (elem.get('alpha-2')):
        alpha = elem.get('alpha-2')
    return alpha

def buildId(elem):
    uniq = random.randint(0,10000)      # Just in case
    alpha = buildAlpha(elem)
    if (alpha):
        uniq=alpha
    return 'GeodesyML_CountryCode-'+uniq

with open(outputFile, 'w') as outfile:
    writeHeader(outfile)
    for elem in tree.getroot().findall('.//country'):
        id = buildId(elem)
        alpha=buildAlpha(elem)
        country=elem.get('name').encode('utf-8')
        alpha2=elem.get('alpha-2')
        alpha3=elem.get('alpha-3')
        code=elem.get('country-code')
        iso=elem.get('iso_3166-2')
        region=elem.get('region')
        subRegion=elem.get('sub-region')

        outfile.write("            <codeEntry>\n")
        outfile.write("                <CodeDefinition gml:id='" + id +"'>\n")
        outfile.write("                    <gml:description>country={} alpha-2={} alpha-3={} country-code={} iso={} region={} sub-region={}</gml:description>\n".format(country, alpha2, alpha3, code, iso, region, subRegion))
        outfile.write("                    <gml:identifier codeSpace='urn:xml-gov-au:icsm:egeodesy:0.4'>"+alpha+"</gml:identifier>\n")
        outfile.write("                </CodeDefinition>\n")
        outfile.write("            </codeEntry>\n")
    writeFooter(outfile)
