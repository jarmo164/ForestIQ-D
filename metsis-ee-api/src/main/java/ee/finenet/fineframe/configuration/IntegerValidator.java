package ee.finenet.fineframe.configuration;

import ee.finenet.fineframe.configuration.validators.NotNullValidator;

public class IntegerValidator implements PropertyValidator {

    public static final ee.finenet.fineframe.configuration.IntegerValidator INSTANCE = new ee.finenet.fineframe.configuration.IntegerValidator();

    private IntegerValidator() {
    }

    @Override
    public void validate(String value) {
        NotNullValidator.INSTANCE.validate(value);
        try {
            Integer.parseInt(value);
        } catch (Exception e) {
            throw new PropertyValidationException("Value was supposed to be of type integer", e);
        }
    }
}
