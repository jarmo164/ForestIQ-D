package ee.metsis.owners;

import ee.finenet.fineframe.http.AbstractRequestHandler;
import ee.finenet.fineframe.http.Requestable;
import ee.metsis.ServiceRegistry;
import ee.metsis.security.LimitedPrivilegesChecks;
import ee.metsis.security.Privilege;
import ee.metsis.ServiceRegistry;
import ee.metsis.security.Privilege;
import spark.Request;
import spark.Response;

import java.util.Collection;

import static ee.metsis.security.LimitedPrivilegesChecks.ownerServiceLimitedPrivilegesCheck;

@Requestable("/owners/:id")
public class GetOwnerRequestHandler extends AbstractRequestHandler {

    private final OwnerService ownerService;

    public GetOwnerRequestHandler(ServiceRegistry serviceRegistry) {
        ownerService = serviceRegistry.getOwnerService();
    }

    @Override
    protected Owner handleRequest(Request req, Response res) {
        LimitedPrivilegesChecks.ownerServiceLimitedPrivilegesCheck(req, ownerService);
        String ownerId = req.params(":id");
        return ownerService.findOwner(ownerId).orElseThrow(OwnerNotFoundException::new);
    }

    @Override
    protected Collection<String> requireAtLeastOneOfPrivileges() {
        return privileges(Privilege.OWNER_PROFILE.name(), Privilege.ASSIGNED_OWNERS.name());
    }
}
