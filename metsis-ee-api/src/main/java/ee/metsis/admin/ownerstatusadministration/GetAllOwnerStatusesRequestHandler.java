package ee.metsis.admin.ownerstatusadministration;

import ee.finenet.fineframe.http.AbstractRequestHandler;
import ee.finenet.fineframe.http.Requestable;
import ee.metsis.ServiceRegistry;
import ee.metsis.security.Privilege;
import spark.Request;
import spark.Response;

import java.util.Collection;

@Requestable("/owner-statuses")
public class GetAllOwnerStatusesRequestHandler extends AbstractRequestHandler {

    private final OwnerStatusService ownerStatusService;

    public GetAllOwnerStatusesRequestHandler(ServiceRegistry serviceRegistry) {
        this.ownerStatusService = serviceRegistry.getOwnerStatusService();
    }

    @Override
    protected Object handleRequest(Request req, Response res) {
        return ownerStatusService.getPossibleOwnerStatuses();
    }

    @Override
    protected Collection<String> requireAtLeastOneOfPrivileges() {
        return privileges(Privilege.ADMIN.name());
    }
}
