package ee.metsis.owners.logservice;

import ee.finenet.fineframe.http.AbstractRequestHandler;
import ee.finenet.fineframe.http.Requestable;
import ee.metsis.ServiceRegistry;
import ee.metsis.owners.OwnerService;
import ee.metsis.security.LimitedPrivilegesChecks;
import ee.metsis.security.Privilege;
import ee.metsis.ServiceRegistry;
import ee.metsis.owners.OwnerService;
import ee.metsis.security.LimitedPrivilegesChecks;
import ee.metsis.security.Privilege;
import spark.Request;
import spark.Response;

import java.util.Collection;
import java.util.List;

@Requestable("/owners/:id/log")
public class GetOwnerLogRequestHandler extends AbstractRequestHandler {

    private final OwnerService ownerService;
    private final OwnerLogService ownerLogService;

    public GetOwnerLogRequestHandler(ServiceRegistry serviceRegistry) {
        this.ownerService = serviceRegistry.getOwnerService();
        this.ownerLogService = serviceRegistry.getOwnerLogService();
    }

    @Override
    protected List<LogMessage> handleRequest(Request req, Response res) {
        LimitedPrivilegesChecks.ownerServiceLimitedPrivilegesCheck(req, ownerService);
        String ownerId = req.params(":id");
        return ownerLogService.getOwnersWorkLog(ownerId, 0L);
    }

    @Override
    protected Collection<String> requireAtLeastOneOfPrivileges() {
        return privileges(Privilege.OWNER_PROFILE.name(), Privilege.ASSIGNED_OWNERS.name());
    }
}
