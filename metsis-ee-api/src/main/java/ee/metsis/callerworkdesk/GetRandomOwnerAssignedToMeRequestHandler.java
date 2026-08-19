package ee.metsis.callerworkdesk;

import ee.finenet.fineframe.exceptions.BadRequestException;
import ee.finenet.fineframe.http.AbstractRequestHandler;
import ee.finenet.fineframe.http.Requestable;
import ee.metsis.ServiceRegistry;
import ee.metsis.owners.OwnerSearchCriteria;
import ee.metsis.owners.OwnerService;
import ee.metsis.security.Privilege;
import spark.Request;
import spark.Response;

import java.util.Collection;

@Requestable("/my-work/next-owner")
public class GetRandomOwnerAssignedToMeRequestHandler extends AbstractRequestHandler {

    private final OwnerService ownerService;

    public GetRandomOwnerAssignedToMeRequestHandler(ServiceRegistry serviceRegistry) {
        this.ownerService = serviceRegistry.getOwnerService();
    }

    @Override
    protected NextAssignedWorkItemResponse handleRequest(Request req, Response res) {
        return ownerService
                .searchOwners(new OwnerSearchCriteria("ASSIGNED", getAuthenticatedUsersId(req), 1L))
                .stream().findAny().map(e -> new NextAssignedWorkItemResponse(e.getId()))
                .orElseThrow(() -> new BadRequestException("NO_MORE_WORK_ASSIGNED_OWNERS_FOR_AUTHENTICATED_USER"));
    }

    @Override
    protected Collection<java.lang.String> requireAtLeastOneOfPrivileges() {
        return privileges(Privilege.ASSIGNED_OWNERS.name());
    }
}
