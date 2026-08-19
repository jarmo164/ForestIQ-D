package ee.metsis.admin;

import ee.finenet.fineframe.exceptions.BadRequestException;
import ee.finenet.fineframe.http.AbstractRequestHandler;
import ee.finenet.fineframe.http.RequestMethod;
import ee.finenet.fineframe.http.Requestable;
import ee.finenet.fineframe.security.password.PasswordHandler;
import ee.finenet.fineframe.user.MaintainableUser;
import ee.finenet.fineframe.user.UserService;
import ee.finenet.fineframe.utilities.StringUtility;
import ee.metsis.ServiceRegistry;
import ee.metsis.security.Privilege;
import spark.Request;
import spark.Response;

import java.util.Collection;

import static ee.finenet.fineframe.serialization.GsonHolder.GSON;

@Requestable(value = "/admin/users", method = RequestMethod.POST)
public class AddUserRequestHandler extends AbstractRequestHandler {

    private final UserService userService;
    private final PasswordHandler passwordHandler;

    public AddUserRequestHandler(ServiceRegistry serviceRegistry) {
        this.userService = serviceRegistry.getUserService();
        this.passwordHandler = serviceRegistry.getPasswordHandler();
    }

    @Override
    public AddUserResponse handleRequest(Request req, Response res) {
        MaintainableUser maintainableUser = GSON.fromJson(req.body(), MaintainableUser.class);
        assertRequestValid(maintainableUser);
        String initialPassword = passwordHandler.createRandomPassword();
        userService.addUser(maintainableUser, passwordHandler.hashPassword(initialPassword));
        return new AddUserResponse(maintainableUser, initialPassword);
    }

    private void assertRequestValid(MaintainableUser user) {
        if (user == null) {
            throw new BadRequestException("ADMIN_ADD_USER_INVALID_ID");
        }
        String userId = user.getId();
        if (!isUserIdValid(userId)) {
            throw new BadRequestException("ADMIN_ADD_USER_INVALID_ID",
                    String.format("Provided user id: '%s'", userId));
        }
        String fullName = user.getName();
        if (!isFullNameValid(fullName)) {
            throw new BadRequestException("ADMIN_ADD_USER_INVALID_FULL_NAME",
                    String.format("Provided full name: '%s'", fullName));
        }
        userService.findById(user.getId()).ifPresent((u) -> {
            throw new BadRequestException("ADMIN_ADD_USER_USER_ALREADY_EXISTS",
                    String.format("Provided user id: '%s'", userId));
        });
    }

    private boolean isUserIdValid(String userId) {
        return !StringUtility.isNullOrBlank(userId) &&
                userId.length() >= 4 &&
                userId.length() <= 50 &&
                userId.matches("^[a-z0-9]*$");
    }

    private boolean isFullNameValid(String fullName) {
        return !StringUtility.isNullOrBlank(fullName) &&
                fullName.length() >= 4 &&
                fullName.length() <= 100;
    }

    @Override
    protected Collection<String> requireAtLeastOneOfPrivileges() {
        return privileges(Privilege.ADMIN.name());
    }
}
