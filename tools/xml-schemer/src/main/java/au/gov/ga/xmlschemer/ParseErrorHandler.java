package au.gov.ga.xmlschemer;

import java.util.ArrayList;
import java.util.List;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.xml.sax.ErrorHandler;
import org.xml.sax.SAXParseException;

public class ParseErrorHandler implements ErrorHandler {

    private static final Logger log = LoggerFactory.getLogger(ParseErrorHandler.class);

    private List<Violation> violations = new ArrayList<>();

    public void error(SAXParseException e) {
        violations.add(extractViolation(e));
    }

    public void fatalError(SAXParseException e) {
        violations.add(extractViolation(e));
    }

    public void warning(SAXParseException e) {
        Violation v = extractViolation(e);
        log.warn(v.getLocation() + ":" + v.getMessage());
    }

    public boolean hasErrors() {
        return !violations.isEmpty();
    }

    public List<Violation> getViolations() {
        return violations;
    }

    private Violation extractViolation(SAXParseException e) {
        return new Violation(e.getSystemId() + ":" + e.getLineNumber() + ":" + e.getColumnNumber(),
                e.getMessage());
    }
}
