package ee.metsis.admin;

import ee.finenet.fineframe.user.MaintainableUser;

public class AddUserResponse {
    private final MaintainableUser user;
    private final String password;

    public AddUserResponse(MaintainableUser user, String password) {
        this.user = user;
        this.password = password;
    }

    public MaintainableUser getUser() {
        return user;
    }

    public String getPassword() {
        return password;
    }
}
