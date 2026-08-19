package ee.finenet.fineframe.configuration.instructions;

import ee.finenet.fineframe.configuration.PropertyTypeReader;

public class LongReadingInstruction implements PropertyTypeReader<Long> {

    public static final ee.finenet.fineframe.configuration.instructions.LongReadingInstruction INSTANCE = new ee.finenet.fineframe.configuration.instructions.LongReadingInstruction();

    private LongReadingInstruction() {
    }

    @Override
    public Long read(String stringValue) {
        try {
            return Long.parseLong(stringValue);
        } catch (Exception e) {
            return null;
        }
    }
}
