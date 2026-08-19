package ee.finenet.fineframe.security.password;

import ee.finenet.fineframe.utilities.StringUtility;

public class UserPasswordRequestModel {

    private final String user;
    private final String password;

    public UserPasswordRequestModel(String user, String password) {
        this.user = user;
        this.password = password;
    }

    public String getUser() {
        return user;
    }

    public String getPassword() {
        return StringUtility.emptyIfNull(password);
    }

}
