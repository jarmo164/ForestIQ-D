package ee.finenet.fineframe.db;

import ee.finenet.fineframe.exceptions.FineFrameException;

public class DatabaseException extends FineFrameException {

    private static final String CODE = "DB_ERROR";

    public DatabaseException(Throwable cause) {
        super(CODE, "Problem communicating with database", cause);
    }
}
