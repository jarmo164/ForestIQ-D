package ee.finenet.fineframe.configuration;

public class PropertyValidationException extends IllegalStateException {
    public PropertyValidationException(String message) {
        super(message);
    }

    PropertyValidationException(String message, Throwable cause) {
        super(message, cause);
    }
}
