package ee.finenet.fineframe.configuration;

public class NoValidaton  implements PropertyValidator {

    public static final ee.finenet.fineframe.configuration.NoValidaton INSTANCE = new ee.finenet.fineframe.configuration.NoValidaton();

    private NoValidaton() {
    }

    @Override
    public void validate(String value) {
    }
}
