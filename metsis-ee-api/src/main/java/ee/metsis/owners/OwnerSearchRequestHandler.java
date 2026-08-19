package ee.metsis.owners;

import ee.finenet.fineframe.http.AbstractRequestHandler;
import ee.finenet.fineframe.http.Requestable;
import ee.metsis.ServiceRegistry;
import ee.metsis.security.Privilege;
import ee.metsis.ServiceRegistry;
import ee.metsis.security.Privilege;
import spark.Request;
import spark.Response;

import java.util.Collection;
import java.util.List;

@Requestable("/owners")
public class OwnerSearchRequestHandler extends AbstractRequestHandler {

    private final OwnerService ownerService;

    public OwnerSearchRequestHandler(ServiceRegistry serviceRegistry) {
        ownerService = serviceRegistry.getOwnerService();
    }

    @Override
    protected List<OwnerMinimal> handleRequest(Request req, Response res) {
        OwnerSearchCriteria ownerSearchCriteria = new OwnerSearchCriteria(req);
        return ownerService.searchOwners(ownerSearchCriteria);
    }

    @Override
    protected Collection<String> requireAtLeastOneOfPrivileges() {
        return privileges(Privilege.OWNER_PROFILE.name());
    }
}
