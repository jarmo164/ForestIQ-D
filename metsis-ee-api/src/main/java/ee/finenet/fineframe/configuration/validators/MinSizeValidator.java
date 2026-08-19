package ee.finenet.fineframe.configuration.validators;

import ee.finenet.fineframe.configuration.IntegerValidator;
import ee.finenet.fineframe.configuration.PropertyValidationException;
import ee.finenet.fineframe.configuration.PropertyValidator;

import static java.lang.String.format;

public class MinSizeValidator implements PropertyValidator {

    private final int minSize;

    public MinSizeValidator(int minSize) {
        this.minSize = minSize;
    }

    @Override
    public void validate(String value) {
        IntegerValidator.INSTANCE.validate(value);
        int i = Integer.parseInt(value);
        if (i < minSize) {
            throw new PropertyValidationException(format("Value was supposed to be smaller than %s, but was %s", minSize, value));
        }
    }
}
