package au.gov.ga.xmlschemer;

import java.util.List;

import javax.xml.transform.stream.StreamSource;

import org.junit.Test;

public class SchemaValidatorTest {

    private static final ClassLoader classLoader = Thread.currentThread().getContextClassLoader();

    private static String getFullFileName(String fileName) {
        return classLoader.getResource(fileName).getFile();
    }

    private List<Violation> getViolations(String xsdFileName, String xmlFileName) throws Exception {
        StreamSource xsd = new StreamSource(getFullFileName(xsdFileName));
        StreamSource xml = new StreamSource(getFullFileName(xmlFileName));
        String catalog = getFullFileName("catalog.xml");
        return new SchemaValidator(xsd, catalog).validate(xml);
    }

    @Test
    public void validateResponsibleParty() throws Exception {
        Asserts.assertNoViolations(getViolations("iso-19139-20070417/gmd/gmd.xsd", "ResponsibleParty-valid.xml"));
    }

    @Test
    public void invalidateResponsibleParty() throws Exception {
        Asserts.assertViolations(getViolations("iso-19139-20070417/gmd/gmd.xsd", "ResponsibleParty-invalid-schema.xml"), 1);
    }
}
