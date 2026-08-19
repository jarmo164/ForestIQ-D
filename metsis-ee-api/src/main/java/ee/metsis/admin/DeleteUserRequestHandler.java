package ee.metsis.admin;

import ee.finenet.fineframe.http.AbstractRequestHandler;
import ee.finenet.fineframe.http.RequestMethod;
import ee.finenet.fineframe.http.Requestable;
import ee.finenet.fineframe.http.genericmodels.OkResponse;
import ee.finenet.fineframe.user.UserService;
import ee.metsis.ServiceRegistry;
import ee.metsis.security.Privilege;
import spark.Request;
import spark.Response;

import java.util.Collection;

@Requestable(value = "/admin/users/:user", method = RequestMethod.DELETE)
public class DeleteUserRequestHandler extends AbstractRequestHandler {

    private final UserService userService;

    public DeleteUserRequestHandler(ServiceRegistry serviceRegistry) {
        this.userService = serviceRegistry.getUserService();
    }

    @Override
    public OkResponse handleRequest(Request req, Response res) {
        String userId = req.params(":user");
        userService.deleteUser(userId);
        return OkResponse.INSTANCE;
    }

    @Override
    protected Collection<String> requireAtLeastOneOfPrivileges() {
        return privileges(Privilege.ADMIN.name());
    }

}
