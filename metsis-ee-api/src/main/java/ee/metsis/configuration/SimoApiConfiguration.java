package ee.metsis.configuration;

import ee.finenet.fineframe.configuration.NoValidaton;
import ee.finenet.fineframe.configuration.PropertyReadingInstruction;
import ee.finenet.fineframe.configuration.StringReadingInstruction;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Properties;

public class SimoApiConfiguration {

    private static final Logger logger = LoggerFactory.getLogger(SimoApiConfiguration.class);

    private final String endpoint;
    private final String token;

    public SimoApiConfiguration(Properties properties) {
        this.endpoint = new PropertyReadingInstruction<>(
                properties,
                "METSIS_SIMO_API_ENDPOINT",
                NoValidaton.INSTANCE,
                StringReadingInstruction.INSTANCE)
                .read();
        this.token = new PropertyReadingInstruction<>(
                properties,
                "METSIS_SIMO_API_TOKEN",
                NoValidaton.INSTANCE,
                StringReadingInstruction.INSTANCE)
                .read();
        logger.info("Configuration loaded endpoint: '" + endpoint + "'; token: '" + token + "'");
    }

    public String getEndpoint() {
        return endpoint;
    }

    public String getToken() {
        return token;
    }
}
