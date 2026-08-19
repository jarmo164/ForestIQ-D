package ee.metsis.admin;

import ee.finenet.fineframe.http.AbstractRequestHandler;
import ee.finenet.fineframe.http.Requestable;
import ee.finenet.fineframe.user.MaintainableUser;
import ee.finenet.fineframe.user.UserService;
import ee.metsis.ServiceRegistry;
import ee.metsis.security.Privilege;
import spark.Request;
import spark.Response;

import java.util.Collection;
import java.util.List;

@Requestable(value = "/admin/users")
public class MaintainUsersRequestHandler extends AbstractRequestHandler {

    private final UserService userService;

    public MaintainUsersRequestHandler(ServiceRegistry serviceRegistry) {
        this.userService = serviceRegistry.getUserService();
    }

    @Override
    public List<MaintainableUser> handleRequest(Request req, Response res) {
        return userService.getAllUsers();
    }

    @Override
    protected Collection<String> requireAtLeastOneOfPrivileges() {
        return privileges(Privilege.ADMIN.name());
    }
}
