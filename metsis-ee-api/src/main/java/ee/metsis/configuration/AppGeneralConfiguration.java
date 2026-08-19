package ee.metsis.configuration;

import ee.finenet.fineframe.configuration.NoValidaton;
import ee.finenet.fineframe.configuration.PortValidator;
import ee.finenet.fineframe.configuration.PropertyReadingInstruction;
import ee.finenet.fineframe.configuration.instructions.BooleanReadingInstruction;
import ee.finenet.fineframe.configuration.instructions.IntegerReadingInstruction;

import java.util.Properties;

public class AppGeneralConfiguration {

    private final int port;
    private final boolean devMode;

    public AppGeneralConfiguration(Properties properties) {
        this.port = new PropertyReadingInstruction<>(
                properties,
                "METSIS_PORT",
                PortValidator.INSTANCE,
                IntegerReadingInstruction.INSTANCE)
                .read();

        this.devMode = new PropertyReadingInstruction<>(
                properties,
                "METSIS_DEVMODE",
                NoValidaton.INSTANCE,
                BooleanReadingInstruction.INSTANCE)
                .read();
    }

    public int getPort() {
        return port;
    }

    public boolean isDevMode() {
        return devMode;
    }
}
