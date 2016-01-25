<?xml version="1.0" encoding="UTF-8"?>
<sch:schema xmlns:sch="http://purl.oclc.org/dsdl/schematron" queryBinding="xslt2">
    <!--
        This Schematron schema looks up the codeList and checks that
        the codeListValue in the XML metadata document are valid
        according to that codeList.
    -->
    <sch:title>Check that the codeList exists and that the codeListValue is in that codeList</sch:title>
    <sch:ns prefix="gml" uri="http://www.opengis.net/gml/3.2" />
    <sch:ns prefix="gmx" uri="http://www.isotc211.org/2005/gmx"/>
    <sch:pattern id="checkCodeList">
        <sch:rule context="//*[@codeList]">
            <sch:let name="codeListDoc" value="document(substring-before(@codeList,'#'))//gmx:CodeListDictionary[@gml:id = substring-after(current()/@codeList,'#')]"/>
            <sch:assert test="$codeListDoc">Unable to find the specified codeList document or CodeListDictionary node.</sch:assert>
            <sch:assert test="@codeListValue = $codeListDoc/gmx:codeEntry/gmx:CodeDefinition/gml:identifier" diagnostics="desc.diag">codeListValue is not in the specified codeList.</sch:assert>
        </sch:rule>
    </sch:pattern>
	
	<sch:diagnostics>
		<sch:diagnostic id="desc.diag">codeListValue doesn't exist: <sch:value-of select="@codeListValue"/></sch:diagnostic>
	</sch:diagnostics>
</sch:schema>
