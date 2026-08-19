package ee.finenet.fineframe.exceptions;

public class ResourceNotFoundException extends FineFrameException {
    public ResourceNotFoundException(String code) {
        super(code);
    }
}
