package ee.metsis.users;

import ee.finenet.fineframe.exceptions.ResourceNotFoundException;

public class UserNotFoundException extends ResourceNotFoundException {

    public static final String CODE = "NO_SUCH_USER";

    public UserNotFoundException() {
        super(CODE);
    }
}
