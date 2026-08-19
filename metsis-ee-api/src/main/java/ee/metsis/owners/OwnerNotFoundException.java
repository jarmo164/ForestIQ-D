package ee.metsis.owners;

import ee.finenet.fineframe.exceptions.ResourceNotFoundException;

public class OwnerNotFoundException extends ResourceNotFoundException {
    private static final String CODE = "OWNER_NOT_FOUND";
    public OwnerNotFoundException() {
        super(CODE);
    }
}
