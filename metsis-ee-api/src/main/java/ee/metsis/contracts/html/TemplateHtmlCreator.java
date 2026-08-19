package ee.metsis.contracts.html;

import ee.metsis.contracts.pdf.ContractInput;
import org.apache.velocity.Template;
import org.apache.velocity.VelocityContext;
import org.apache.velocity.app.VelocityEngine;
import org.apache.velocity.runtime.RuntimeConstants;
import org.apache.velocity.runtime.resource.loader.ClasspathResourceLoader;

import java.io.StringWriter;

public class TemplateHtmlCreator {
    private final VelocityEngine ve = new VelocityEngine();

    public TemplateHtmlCreator() {
        ve.setProperty(RuntimeConstants.RESOURCE_LOADER, "classpath");
        ve.setProperty("classpath.resource.loader.class", ClasspathResourceLoader.class.getName());
    }

    public String create(ContractInput contract) {
        try {
            Template template = ve.getTemplate("contract-templates/tm-energy.vm");
            VelocityContext context = new VelocityContext();
            context.put("contract", contract);
            StringWriter writer = new StringWriter();
            template.merge(context, writer);
            writer.flush();
            writer.close();
            return writer.toString();
        } catch (Exception e) {
            throw new RuntimeException("Creating HTML with Velocity failed", e);
        }
    }
}
