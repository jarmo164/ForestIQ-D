package ee.finenet.fineframe.exceptions;

public class ForbiddenException extends FineFrameException {

    public static final String CODE_AUTH_FAIL_NO_USERNAME = "AUTH_FAIL_NO_USERNAME";
    public static final String CODE_AUTH_FAIL_NO_PASSWORD = "CODE_AUTH_FAIL_NO_PASSWORD";
    public static final String CODE_NOT_ENOUGH_PRIVILEGES = "NOT_ENOUGH_PRIVILEGES";
    public static final String CODE_AUTH_FAIL_WRONG_PASSWORD = "AUTH_FAIL_WRONG_PASSWORD";
    public static final String CODE_AUTH_FAILED_TOTP_OFF = "AUTH_FAILED_TOTP_OFF";
    public static final String CODE_AUTH_FAILED_WRONG_TOTP_CODE = "AUTH_FAILED_WRONG_TOTP_CODE";
    public static final String CODE_AUTH_FAIL_NO_TOKEN = "AUTH_FAIL_NO_TOKEN";
    public static final String CODE_AUTH_FAIL_NO_SUCH_USER = "AUTH_FAIL_NO_SUCH_USER";

    public ForbiddenException(String code) {
        super(code);
    }

    public ForbiddenException(String code, Throwable cause) {
        super(code, cause);
    }

    public ForbiddenException(String code, String message, Throwable cause) {
        super(code, message, cause);
    }

    public ForbiddenException(String code, String message) {
        super(code, message);
    }
}
