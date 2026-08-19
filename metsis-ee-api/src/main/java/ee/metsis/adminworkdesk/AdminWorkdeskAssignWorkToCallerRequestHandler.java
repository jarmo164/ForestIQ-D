package ee.metsis.adminworkdesk;

import ee.finenet.fineframe.exceptions.BadRequestException;
import ee.finenet.fineframe.http.AbstractRequestHandler;
import ee.finenet.fineframe.http.RequestMethod;
import ee.finenet.fineframe.http.Requestable;
import ee.finenet.fineframe.http.genericmodels.OkResponse;
import ee.finenet.fineframe.user.UserService;
import ee.finenet.fineframe.utilities.CollectionUtility;
import ee.finenet.fineframe.utilities.StringUtility;
import ee.metsis.ServiceRegistry;
import ee.metsis.ServiceRegistry;
import ee.metsis.owners.OwnerService;
import ee.metsis.security.Privilege;
import spark.Request;
import spark.Response;

import java.util.Collection;

import static ee.finenet.fineframe.serialization.GsonHolder.GSON;

@Requestable(value = "/admin-workdesk/assign", method = RequestMethod.POST)
public class AdminWorkdeskAssignWorkToCallerRequestHandler extends AbstractRequestHandler {

    private final UserService userService;
    private final OwnerService ownerService;

    public AdminWorkdeskAssignWorkToCallerRequestHandler(ServiceRegistry serviceRegistry) {
        this.userService = serviceRegistry.getUserService();
        this.ownerService = serviceRegistry.getOwnerService();
    }

    @Override
    protected OkResponse handleRequest(Request req, Response res) {
        AssignWorkModel request = GSON.fromJson(req.body(), AssignWorkModel.class);
        assertRequestValid(request);
        ownerService.assignWorkToCaller(request, getAuthToken(req).getUserId());
        return OkResponse.INSTANCE;
    }

    private void assertRequestValid(AssignWorkModel request) {
        String assignee = request.getAssignee();
        if (StringUtility.isNullOrBlank(assignee)) {
            throw new BadRequestException("ADMIN_ASSIGN_WORK_TO_CALLER_NO_ASSIGNEE");
        }
        if (!userService.findById(assignee).isPresent()) {
            throw new BadRequestException("ADMIN_ASSIGN_WORK_TO_CALLER_NO_SUCH_ASSIGNEE");
        }
        if (CollectionUtility.emptyIfNull(request.getOwners()).isEmpty()) {
            throw new BadRequestException("ADMIN_ASSIGN_WORK_TO_CALLER_NO_OWNERS");
        }
    }

    @Override
    protected Collection<String> requireAtLeastOneOfPrivileges() {
        return privileges(Privilege.ADMIN.name());
    }
}
