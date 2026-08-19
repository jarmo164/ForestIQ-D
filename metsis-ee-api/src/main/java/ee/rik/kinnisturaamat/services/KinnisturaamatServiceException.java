package ee.rik.kinnisturaamat.services;

public class KinnisturaamatServiceException extends RuntimeException {

    public KinnisturaamatServiceException(String message, Throwable cause) {
        super(message, cause);
    }

    public KinnisturaamatServiceException(String message) {
        super(message);
    }
}
