package ee.finenet.fineframe.configuration;

public class PortValidator implements PropertyValidator {

    public static final ee.finenet.fineframe.configuration.PortValidator INSTANCE = new ee.finenet.fineframe.configuration.PortValidator();

    private PortValidator() {
    }

    @Override
    public void validate(String value) {
        IntegerValidator.INSTANCE.validate(value);
        int port = Integer.parseInt(value);
        if (port < 0 || port > 65535) {
            throw new PropertyValidationException(
                    String.format("Value is supposed to be network port, which means it cant be smaller than 0 and larger than 65535, but it was %s", port));
        }
    }
}
