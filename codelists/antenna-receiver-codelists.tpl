<CT_CodelistCatalogue
    xmlns="http://www.isotc211.org/2005/gmx"
    xmlns:gco="http://www.isotc211.org/2005/gco"
    xmlns:gml="http://www.opengis.net/gml/3.2"
    xmlns:xlink="http://www.w3.org/1999/xlink"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">

    <bind tag="eGeodesyCodeSpace">urn:xml-gov-au:icsm:egeodesy:0.3</bind>

    <name>
        <gco:CharacterString>GeodesyML GNSS antenna and receiver type codes</gco:CharacterString>
    </name>
    <scope>
        <gco:CharacterString>eGeodesy</gco:CharacterString>
    </scope>
    <fieldOfApplication>
        <gco:CharacterString>Geodesy</gco:CharacterString>
    </fieldOfApplication>
    <versionNumber>
        <gco:CharacterString>0.3</gco:CharacterString>
    </versionNumber>
    <versionDate>
        <gco:Date>2015-12-22</gco:Date>
    </versionDate>
    <codelistItem>
        <CodeListDictionary gml:id="GeodesyML_GNSSReceiverTypeCode">
            <gml:description>GeodesyML GNSS Receiver Types</gml:description>
            <gml:identifier codeSpace="${eGeodesyCodeSpace}">GeodesyML_GNSSReceiverTypeCode</gml:identifier>
            <ReceiverTypeCodes>
                <codeEntry>
                    <CodeDefinition gml:id="${id}">
                        <gml:description><desc/></gml:description>
                        <gml:identifier codeSpace="${eGeodesyCodeSpace}"><id/></gml:identifier>
                        <gml:name><name/></gml:name>
                    </CodeDefinition>
                </codeEntry>
            </ReceiverTypeCodes>
        </CodeListDictionary>
    </codelistItem>
    <codelistItem>
        <CodeListDictionary gml:id="GeodesyML_GNSSAntennaTypeCode">
            <gml:description>GeodesyML GNSS Antenna Type Codes</gml:description>
            <gml:identifier codeSpace="${eGeodesyCodeSpace}">GeodesyML_GNSSAntennaTypeCode</gml:identifier>
            <AntennaTypeCodes>
                <codeEntry >
                    <CodeDefinition gml:id="${id}">
                        <gml:description><desc/></gml:description>
                        <gml:identifier codeSpace="${eGeodesyCodeSpace}"><id/></gml:identifier>
                        <gml:name><name/></gml:name>
                    </CodeDefinition>
                </codeEntry>
            </AntennaTypeCodes>
        </CodeListDictionary>
    </codelistItem>
</CT_CodelistCatalogue>
