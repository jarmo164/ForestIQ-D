package ee.rik.uuskinnisturaamat.services;

public class UusKinnisturaamatServiceException  extends RuntimeException {

    public UusKinnisturaamatServiceException(String message, Throwable cause) {
        super(message, cause);
    }

    public UusKinnisturaamatServiceException(String message) {
        super(message);
    }
}
