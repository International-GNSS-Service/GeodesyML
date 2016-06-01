package au.gov.ga.xmlschemer;

import java.io.InputStream;
import java.util.List;

import javax.xml.transform.stream.StreamSource;

import org.junit.Test;

public class SchematronValidatorTest {

    private StreamSource schematron = new StreamSource(getResourceStream("codeListValidation.sch.xsl"));
    private SchematronValidator validator = new SchematronValidator(schematron, getResourceFileName("catalog.xml"));

    private static ClassLoader classLoader = Thread.currentThread().getContextClassLoader();

    private static InputStream getResourceStream(String resource) {
        return classLoader.getResourceAsStream(resource);
    }

    private static String getResourceFileName(String resource) {
        return classLoader.getResource(resource).getFile();
    }

    private List<Violation> getViolations(String xmlFileName) throws Exception {
        StreamSource xml = new StreamSource(getResourceStream(xmlFileName));
        return validator.validate(xml);
    }

    @Test
    public void validateResponsibleParty() throws Exception {
        Asserts.assertNoViolations(getViolations("ResponsibleParty-valid.xml"));
    }

    @Test
    public void invalidateResponsibleParty() throws Exception {
        Asserts.assertViolations(getViolations("ResponsibleParty-invalid-schematron.xml"), 1);
    }
}
