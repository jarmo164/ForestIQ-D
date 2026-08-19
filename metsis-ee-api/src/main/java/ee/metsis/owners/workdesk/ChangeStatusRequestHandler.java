package ee.metsis.owners.workdesk;

import ee.finenet.fineframe.http.AbstractRequestHandler;
import ee.finenet.fineframe.http.RequestMethod;
import ee.finenet.fineframe.http.Requestable;
import ee.finenet.fineframe.http.genericmodels.OkResponse;
import ee.finenet.fineframe.user.UserMinimal;
import ee.metsis.ServiceRegistry;
import ee.metsis.owners.Owner;
import ee.metsis.owners.OwnerNotFoundException;
import ee.metsis.owners.OwnerService;
import ee.metsis.security.LimitedPrivilegesChecks;
import ee.metsis.security.Privilege;
import ee.metsis.users.statistics.UserStatisticsService;
import spark.Request;
import spark.Response;

import java.util.Collection;
import java.util.Optional;

import static ee.finenet.fineframe.serialization.GsonHolder.GSON;

@Requestable(value = "/owners/:id/change-status", method = RequestMethod.POST)
public class ChangeStatusRequestHandler extends AbstractRequestHandler {

    private final OwnerService ownerService;
    private final UserStatisticsService userStatisticsService;

    public ChangeStatusRequestHandler(ServiceRegistry serviceRegistry) {
        this.ownerService = serviceRegistry.getOwnerService();
        this.userStatisticsService = serviceRegistry.getUserStatisticsService();
    }

    @Override
    protected Object handleRequest(Request req, Response res) {
        LimitedPrivilegesChecks.ownerServiceLimitedPrivilegesCheck(req, ownerService);
        java.lang.String ownerId = req.params(":id");
        ChangeOwnerStatusModel reqModel = GSON.fromJson(req.body(), ChangeOwnerStatusModel.class);
        java.lang.String authenticatedUsersId = getAuthenticatedUsersId(req);
        Owner owner = ownerService.findOwner(ownerId).orElseThrow(OwnerNotFoundException::new);
        String ownersCurrentStatus = owner.getStatus();
        String ownersNewStatus = reqModel.getNewStatus();
        if (!ownersCurrentStatus.equals(ownersNewStatus)) {
            ownerService.setOwnerStatus(ownerId, ownersNewStatus, reqModel.getComment(), authenticatedUsersId, Optional.ofNullable(owner.getAssignee()).map(UserMinimal::getId).orElse(null));
            userStatisticsService.createUserOwnerStatusChangeRecord(authenticatedUsersId, ownersCurrentStatus, ownersNewStatus);
        }
        return OkResponse.INSTANCE;
    }

    @Override
    protected Collection<java.lang.String> requireAtLeastOneOfPrivileges() {
        return privileges(Privilege.OWNER_PROFILE.name(), Privilege.ASSIGNED_OWNERS.name());
    }
}
