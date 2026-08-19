package ee.metsis.owners.workdesk;

import ee.finenet.fineframe.exceptions.BadRequestException;
import ee.finenet.fineframe.http.AbstractRequestHandler;
import ee.finenet.fineframe.http.RequestMethod;
import ee.finenet.fineframe.http.Requestable;
import ee.finenet.fineframe.http.genericmodels.OkResponse;
import ee.finenet.fineframe.serialization.GsonHolder;
import ee.finenet.fineframe.user.UserMinimal;
import ee.finenet.fineframe.user.UserService;
import ee.metsis.ServiceRegistry;
import ee.metsis.adminworkdesk.AssignWorkModel;
import ee.metsis.owners.OwnerNotFoundException;
import ee.metsis.owners.OwnerService;
import ee.metsis.security.Privilege;
import ee.metsis.users.UserNotFoundException;
import ee.metsis.ServiceRegistry;
import ee.metsis.adminworkdesk.AssignWorkModel;
import ee.metsis.owners.OwnerNotFoundException;
import ee.metsis.owners.OwnerService;
import ee.metsis.security.Privilege;
import ee.metsis.users.UserNotFoundException;
import spark.Request;
import spark.Response;

import java.util.Collection;
import java.util.Collections;
import java.util.Map;


@Requestable(value = "/owner/:id/assignee", method = RequestMethod.POST)
public class AssignOwnerRequestHandler extends AbstractRequestHandler {

    private final OwnerService ownerService;
    private final UserService userService;

    public AssignOwnerRequestHandler(ServiceRegistry serviceRegistry) {
        this.ownerService = serviceRegistry.getOwnerService();
        this.userService = serviceRegistry.getUserService();
    }

    @Override
    protected OkResponse handleRequest(Request req, Response res) {
        String ownerId = req.params(":id");
        String assignee = (String) GsonHolder.GSON.fromJson(req.body(), Map.class).get("assignee");
        assertRequestValid(ownerId, assignee);
        AssignWorkModel assignWorkModel = new AssignWorkModel();
        assignWorkModel.setOwners(Collections.singletonList(ownerId));
        assignWorkModel.setAssignee(assignee);
        assignWorkModel.setReassign(true);
        ownerService.assignWorkToCaller(assignWorkModel, getAuthToken(req).getUserId());
        return OkResponse.INSTANCE;
    }

    private void assertRequestValid(String owner, String assignee) {
        if (!userService.findById(assignee).isPresent()) {
            throw new BadRequestException(UserNotFoundException.CODE);
        }
        UserMinimal currentAssignee = ownerService.findOwner(owner).orElseThrow(OwnerNotFoundException::new).getAssignee();
        if (currentAssignee != null && currentAssignee.getId().equals(assignee)) {
            throw new BadRequestException("CAN_NOT_REASSIGN_WORK_FROM_USER_TO_ITSELF");
        }
    }

    @Override
    protected Collection<String> requireAtLeastOneOfPrivileges() {
        return privileges(Privilege.ADMIN.name());
    }
}
