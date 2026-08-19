package ee.finenet.fineframe.configuration.instructions;

import ee.finenet.fineframe.configuration.PropertyTypeReader;

public class BooleanReadingInstruction implements PropertyTypeReader<Boolean> {

    public static final ee.finenet.fineframe.configuration.instructions.BooleanReadingInstruction INSTANCE = new ee.finenet.fineframe.configuration.instructions.BooleanReadingInstruction();

    private BooleanReadingInstruction() {
    }

    @Override
    public Boolean read(String stringValue) {
        try {
            return Boolean.parseBoolean(stringValue);
        } catch (Exception e) {
            return null;
        }
    }
}
