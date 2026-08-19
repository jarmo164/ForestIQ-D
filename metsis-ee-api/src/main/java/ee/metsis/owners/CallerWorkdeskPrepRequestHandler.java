package ee.metsis.owners;

import ee.finenet.fineframe.http.AbstractRequestHandler;
import ee.finenet.fineframe.http.Requestable;
import ee.metsis.ServiceRegistry;
import ee.metsis.admin.ownerstatusadministration.OwnerStatusService;
import ee.metsis.security.Privilege;
import spark.Request;
import spark.Response;

import java.util.Collection;
import java.util.Collections;

@Requestable("/caller-workdesk-prep-data")
public class CallerWorkdeskPrepRequestHandler extends AbstractRequestHandler {

    private final OwnerStatusService ownerStatusService;

    public CallerWorkdeskPrepRequestHandler(ServiceRegistry serviceRegistry) {
        this.ownerStatusService = serviceRegistry.getOwnerStatusService();
    }

    @Override
    protected Object handleRequest(Request req, Response res) {
        return Collections.singletonMap("statuses", ownerStatusService.getPossibleOwnerStatusIds());
    }

    @Override
    protected Collection<String> requireAtLeastOneOfPrivileges() {
        return privileges(Privilege.OWNER_PROFILE.name(), Privilege.ASSIGNED_OWNERS.name());
    }
}
