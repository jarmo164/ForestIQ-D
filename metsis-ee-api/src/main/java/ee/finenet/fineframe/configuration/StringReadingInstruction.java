package ee.finenet.fineframe.configuration;

public class StringReadingInstruction implements PropertyTypeReader<String> {

    public static final ee.finenet.fineframe.configuration.StringReadingInstruction INSTANCE = new ee.finenet.fineframe.configuration.StringReadingInstruction();

    private StringReadingInstruction() {
    }

    @Override
    public String read(String stringValue) {
        return stringValue;
    }
}
