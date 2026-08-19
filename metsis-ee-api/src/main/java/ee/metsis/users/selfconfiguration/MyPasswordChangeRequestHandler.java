package ee.metsis.users.selfconfiguration;

import ee.finenet.fineframe.http.AbstractRequestHandler;
import ee.finenet.fineframe.http.RequestMethod;
import ee.finenet.fineframe.http.Requestable;
import ee.finenet.fineframe.http.genericmodels.OkResponse;
import ee.finenet.fineframe.security.AuthenticationService;
import ee.finenet.fineframe.security.password.ChangePasswordModel;
import ee.finenet.fineframe.serialization.GsonHolder;
import ee.metsis.ServiceRegistry;
import spark.Request;
import spark.Response;

import java.util.Collection;

@Requestable(value = "/change-my-password", method = RequestMethod.POST)
public class MyPasswordChangeRequestHandler extends AbstractRequestHandler {

    private final AuthenticationService authenticationService;

    public MyPasswordChangeRequestHandler(ServiceRegistry serviceRegistry) {
        this.authenticationService = serviceRegistry.getAuthenticationService();
    }

    @Override
    protected Object handleRequest(Request req, Response res) {
        ChangePasswordModel changePasswordModel = GsonHolder.GSON.fromJson(req.body(), ChangePasswordModel.class);
        authenticationService.changeUsersPassword(getAuthToken(req).getUserId(), changePasswordModel);
        return OkResponse.INSTANCE;
    }

    @Override
    protected Collection<String> requireAtLeastOneOfPrivileges() {
        return noPrivilegesRequired();
    }
}
