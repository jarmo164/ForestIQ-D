package ee.finenet.fineframe.configuration.instructions;

import ee.finenet.fineframe.configuration.PropertyTypeReader;

public class IntegerReadingInstruction implements PropertyTypeReader<Integer> {

    public static final ee.finenet.fineframe.configuration.instructions.IntegerReadingInstruction INSTANCE = new ee.finenet.fineframe.configuration.instructions.IntegerReadingInstruction();

    private IntegerReadingInstruction() {
    }

    @Override
    public Integer read(String stringValue) {
        try {
            return Integer.parseInt(stringValue);
        } catch (Exception e) {
            return null;
        }
    }
}
