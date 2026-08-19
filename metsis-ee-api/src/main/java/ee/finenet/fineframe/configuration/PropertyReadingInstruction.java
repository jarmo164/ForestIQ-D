package ee.finenet.fineframe.configuration;

import ee.finenet.fineframe.exceptions.ConfigurationException;

import java.util.Collections;
import java.util.List;
import java.util.Properties;

public class PropertyReadingInstruction<PROPERTY_TYPE> {

    private final Properties properties;
    private final String propertyName;
    private final List<PropertyValidator> validators;
    private final PropertyTypeReader<PROPERTY_TYPE> typeReader;

    private PropertyReadingInstruction(Properties properties, String propertyName, List<PropertyValidator> validators,
                                       PropertyTypeReader<PROPERTY_TYPE> typeReader) {
        this.properties = properties;
        this.propertyName = propertyName;
        this.validators = validators;
        this.typeReader = typeReader;
    }

    public PropertyReadingInstruction(Properties properties, String propertyName, PropertyValidator validator,
                                      PropertyTypeReader<PROPERTY_TYPE> typeReader) {
        this(properties, propertyName, Collections.singletonList(validator), typeReader);
    }

    public PROPERTY_TYPE read() {
        String stringValue = properties.getProperty(propertyName);
        validators.forEach(v -> {
            try {
                v.validate(stringValue);
            } catch (PropertyValidationException e) {
                throw new ConfigurationException(String.format("Validation of property '%s' failed", propertyName), e);
            }
        });
        return typeReader.read(stringValue);
    }
}
