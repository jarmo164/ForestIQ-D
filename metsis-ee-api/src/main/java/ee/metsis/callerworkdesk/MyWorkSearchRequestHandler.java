package ee.metsis.callerworkdesk;

import ee.finenet.fineframe.http.AbstractRequestHandler;
import ee.finenet.fineframe.http.Requestable;
import ee.metsis.ServiceRegistry;
import ee.metsis.ServiceRegistry;
import ee.metsis.owners.OwnerSearchCriteria;
import ee.metsis.owners.OwnerService;
import ee.metsis.security.Privilege;
import spark.Request;
import spark.Response;

import java.util.Collection;

@Requestable("/my-work")
public class MyWorkSearchRequestHandler extends AbstractRequestHandler {

    private static final int ABSOLUTE_MAX_NUMBER_OF_RESULTS = 100000;
    private final OwnerService ownerService;

    public MyWorkSearchRequestHandler(ServiceRegistry serviceRegistry) {
        this.ownerService = serviceRegistry.getOwnerService();
    }

    @Override
    protected Object handleRequest(Request req, Response res) {
        OwnerSearchCriteria ownerSearchCriteria = new OwnerSearchCriteria(req);
        ownerSearchCriteria.setAssignee(getAuthenticatedUsersId(req));
        ownerSearchCriteria.setLimit(ABSOLUTE_MAX_NUMBER_OF_RESULTS);
        return ownerService.searchOwners(ownerSearchCriteria);
    }

    @Override
    protected Collection<String> requireAtLeastOneOfPrivileges() {
        return privileges(Privilege.OWNER_PROFILE.name(), Privilege.ASSIGNED_OWNERS.name());
    }
}
