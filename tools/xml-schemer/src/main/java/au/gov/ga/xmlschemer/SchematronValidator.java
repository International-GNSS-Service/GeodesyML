package au.gov.ga.xmlschemer;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

import javax.xml.transform.Source;
import javax.xml.xpath.XPath;
import javax.xml.xpath.XPathConstants;
import javax.xml.xpath.XPathExpressionException;
import javax.xml.xpath.XPathFactory;

import org.apache.xerces.dom.DocumentImpl;
import org.apache.xml.resolver.CatalogManager;
import org.apache.xml.resolver.tools.CatalogResolver;
import org.checkerframework.checker.nullness.qual.Nullable;
import org.w3c.dom.Document;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;

import net.sf.saxon.s9api.DOMDestination;
import net.sf.saxon.s9api.Processor;
import net.sf.saxon.s9api.SaxonApiException;
import net.sf.saxon.s9api.XsltTransformer;

public class SchematronValidator implements Validator {

    private Source schematron;
    private @Nullable String catalogFileName;

    public SchematronValidator(Source schematron, @Nullable String catalogFileName) {
        this.schematron = schematron;
        this.catalogFileName = catalogFileName;
    }

    public List<Violation> validate(Source xml) throws IOException {
        try {
            XsltTransformer transformer = new Processor(false).newXsltCompiler()
                .compile(schematron)
                .load();

            // TODO: consolidate with catalog loading in SchemaValidator
            CatalogManager catalogManager = new CatalogManager();
            catalogManager.setIgnoreMissingProperties(true);

            if (catalogFileName != null) {
                catalogManager.setCatalogFiles(catalogFileName);
                transformer.setURIResolver(new CatalogResolver(catalogManager));
            }
            transformer.setSource(xml);
            Document document = new DocumentImpl();
            transformer.setDestination(new DOMDestination(document));

            transformer.transform();

            XPath path = XPathFactory.newInstance().newXPath();
            NodeList failedAsserts = (NodeList) path.evaluate("//*[local-name()='failed-assert']", document, XPathConstants.NODESET);

            List<Violation> violations = new ArrayList<>();

            for (int i = 0; i < failedAsserts.getLength(); i++) {
                Node failedAssert = failedAsserts.item(i);
                violations.add(new Violation(
                    path.evaluate("@location", failedAssert),
                    path.evaluate("text()",    failedAssert)
                ));
            }
            return violations;
        }
        catch (SaxonApiException | XPathExpressionException e) {
            throw new RuntimeException(e);
        }
    }
}
