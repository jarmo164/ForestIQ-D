package ee.finenet.fineframe.exceptions;

public class UnexpextedException extends FineFrameException {

    public static final String CODE = "UNKNOWN_ERROR";

    public UnexpextedException(String message) {
        super(CODE, message);
    }

    public UnexpextedException(String message, Throwable cause) {
        super(CODE, message, cause);
    }

}
