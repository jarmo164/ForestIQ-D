package ee.finenet.fineframe.configuration;

import ee.finenet.fineframe.exceptions.ConfigurationException;

import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.Objects;
import java.util.Properties;

public class PropertyLoader {

    public static Properties loadProperties(String filePath) {
        Objects.requireNonNull(filePath, "filePath in PropertyLoader.loadProperties(filePath) may not be null");
        try (FileInputStream is = new FileInputStream(filePath)){
            return loadProperties(is);
        } catch (IOException e) {
            throw new ConfigurationException("There was a problem loading properties file", e);
        }
    }

    public static Properties loadProperties(InputStream is) {
        Properties properties = new Properties();
        try {
            properties.load(new InputStreamReader(is, StandardCharsets.UTF_8));
        } catch (Exception e) {
            throw new ConfigurationException("There was a problem loading properties stream", e);
        }
        return properties;
    }

}
