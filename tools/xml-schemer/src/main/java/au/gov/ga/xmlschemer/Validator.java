package au.gov.ga.xmlschemer;

import java.io.IOException;
import java.util.List;

import javax.xml.transform.Source;

public interface Validator {
    List<Violation> validate(Source xml) throws IOException;
}
