package ee.finenet.fineframe.exceptions;

public class BadRequestException extends FineFrameException {

    public static final String CODE_CHANGE_MY_PASSWORD_WRONG_OLD_PASSWORD = "CHANGE_MY_PASSWORD_WRONG_OLD_PASSWORD";
    public static final String CODE_CHANGE_MY_PASSWORD_NEW_PASSWORD_INVALID = "CHANGE_MY_PASSWORD_NEW_PASSWORD_INVALID";
    public static final String CODE_CHANGE_MY_PASSWORD_NEW_PASSWORD_NEW_PASSWORD_AGAIN_MISMATCH = "CHANGE_MY_PASSWORD_NEW_PASSWORD_NEW_PASSWORD_AGAIN_MISMATCH";

    public BadRequestException(String code) {
        super(code);
    }

    public BadRequestException(String code, Throwable cause) {
        super(code, cause);
    }

    public BadRequestException(String code, String message, Throwable cause) {
        super(code, message, cause);
    }

    public BadRequestException(String code, String message) {
        super(code, message);
    }
}
