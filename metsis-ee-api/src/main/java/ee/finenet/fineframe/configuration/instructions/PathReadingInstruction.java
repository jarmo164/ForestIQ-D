package ee.finenet.fineframe.configuration.instructions;

import ee.finenet.fineframe.configuration.PropertyTypeReader;

import java.nio.file.Path;
import java.nio.file.Paths;

public class PathReadingInstruction implements PropertyTypeReader<Path> {

    public static final ee.finenet.fineframe.configuration.instructions.PathReadingInstruction INSTANCE = new ee.finenet.fineframe.configuration.instructions.PathReadingInstruction();

    private PathReadingInstruction() {
    }

    @Override
    public Path read(String stringValue) {
        try {
            return Paths.get(stringValue);
        } catch (Exception e) {
            return null;
        }
    }
}
