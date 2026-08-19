package ee.finenet.fineframe.exceptions;

public class ConfigurationException extends IllegalStateException {

    public ConfigurationException(String message) {
        super(String.format("There was a problem with application configuration: %s", message));
    }

    public ConfigurationException(String message, Exception cause) {
        super(String.format("There was a problem with application configuration: %s", message), cause);
    }
}
