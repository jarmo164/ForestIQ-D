package ee.finenet.fineframe.configuration.validators;

import ee.finenet.fineframe.configuration.PropertyValidationException;
import ee.finenet.fineframe.configuration.PropertyValidator;

public class NotNullValidator implements PropertyValidator {

    public static final ee.finenet.fineframe.configuration.validators.NotNullValidator INSTANCE = new ee.finenet.fineframe.configuration.validators.NotNullValidator();

    private NotNullValidator() {
    }

    @Override
    public void validate(String value) {
        if (value == null) {
            throw new PropertyValidationException("Value was null");
        }
    }
}
