package ee.finenet.fineframe.db;

import ee.finenet.fineframe.configuration.NotEmptyValidator;
import ee.finenet.fineframe.configuration.PropertyReadingInstruction;
import ee.finenet.fineframe.configuration.StringReadingInstruction;

import java.util.Objects;
import java.util.Properties;

public class DatabaseConfiguration {

    private final String url;
    private final String user;
    private final String password;

    public DatabaseConfiguration(Properties properties) {
        Objects.requireNonNull(properties, "DatabaseConfiguration.properties may not be null");
        this.url = new PropertyReadingInstruction<>(
                properties,
                "FINEFRAME_DB_URL",
                NotEmptyValidator.INSTANCE,
                StringReadingInstruction.INSTANCE)
                .read();
        this.user = new PropertyReadingInstruction<>(
                properties,
                "FINEFRAME_DB_USER",
                NotEmptyValidator.INSTANCE,
                StringReadingInstruction.INSTANCE)
                .read();
        this.password = new PropertyReadingInstruction<>(
                properties,
                "FINEFRAME_DB_PASSWORD",
                NotEmptyValidator.INSTANCE,
                StringReadingInstruction.INSTANCE).read();
    }

    public String getUrl() {
        return url;
    }

    public String getUser() {
        return user;
    }

    public String getPassword() {
        return password;
    }
}
