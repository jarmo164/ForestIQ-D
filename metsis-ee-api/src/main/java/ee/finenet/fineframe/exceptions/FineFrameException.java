package ee.finenet.fineframe.exceptions;

public class FineFrameException extends RuntimeException {

    private final String code;

    public FineFrameException(String code) {
        super(formatMessage(code, null));
        this.code = code;
    }

    public FineFrameException(String code, Throwable cause) {
        super(formatMessage(code, null), cause);
        this.code = code;
    }

    public FineFrameException(String code, String message, Throwable cause) {
        super(formatMessage(code, message), cause);
        this.code = code;
    }

    public FineFrameException(String code, String message) {
        super(formatMessage(code, message));
        this.code = code;
    }

    public String getCode() {
        return code;
    }

    private static String formatMessage(String code, String message) {
        if (code == null && message == null) {
            throw new IllegalArgumentException("Either exception code or exception message must be set");
        }
        StringBuilder messageBuilder = new StringBuilder();
        if (code != null) {
            messageBuilder.append(String.format("Exception code: '%s'", code));
            if (message != null) {
                messageBuilder.append(": ");
            }
        }
        if (message != null) {
            messageBuilder.append(message);
        }
        return messageBuilder.toString();
    }
}
