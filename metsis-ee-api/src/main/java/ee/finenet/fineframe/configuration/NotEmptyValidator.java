package ee.finenet.fineframe.configuration;

import ee.finenet.fineframe.configuration.validators.NotNullValidator;

public class NotEmptyValidator implements PropertyValidator {

    public static final ee.finenet.fineframe.configuration.NotEmptyValidator INSTANCE = new ee.finenet.fineframe.configuration.NotEmptyValidator();

    private NotEmptyValidator() {
    }

    @Override
    public void validate(String value) {
        NotNullValidator.INSTANCE.validate(value);
        if (value.isEmpty()) {
            throw new PropertyValidationException("Value was empty");
        }
    }
}
