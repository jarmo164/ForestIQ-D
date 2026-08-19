package ee.finenet.fineframe.http.genericmodels;

import ee.finenet.fineframe.exceptions.FineFrameException;
import ee.finenet.fineframe.exceptions.UnexpextedException;

public class ErrorModel {

    private final String code;
    private final String message;

    public ErrorModel(FineFrameException exception) {
        this(exception.getCode(), exception.getMessage());
    }

    protected ErrorModel(String code, String message) {
        this.code = code;
        this.message = message;
    }

    public ErrorModel() {
        this(UnexpextedException.CODE, "Unexpected error");
    }

    public String getCode() {
        return code;
    }

    public String getMessage() {
        return message;
    }
}
