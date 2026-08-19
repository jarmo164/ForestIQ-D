package ee.finenet.fineframe.exceptions;

public class UnauthorizedException extends FineFrameException {

    private static final String CODE = "AUTH_FAIL_INVALID_TOKEN";

    public UnauthorizedException() {
        super(CODE);
    }

    public UnauthorizedException(Throwable cause) {
        super(CODE, cause);
    }
}
