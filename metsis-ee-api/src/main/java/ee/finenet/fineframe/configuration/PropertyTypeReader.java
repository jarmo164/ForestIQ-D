package ee.finenet.fineframe.configuration;

public interface PropertyTypeReader<PROPERTY_TYPE> {
    PROPERTY_TYPE read(String stringValue);
}
