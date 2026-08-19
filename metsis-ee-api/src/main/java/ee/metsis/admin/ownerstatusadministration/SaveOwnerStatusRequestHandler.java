package ee.metsis.admin.ownerstatusadministration;

import ee.finenet.fineframe.http.AbstractRequestHandler;
import ee.finenet.fineframe.http.RequestMethod;
import ee.finenet.fineframe.http.Requestable;
import ee.finenet.fineframe.http.genericmodels.OkResponse;
import ee.finenet.fineframe.serialization.GsonHolder;
import ee.metsis.ServiceRegistry;
import ee.metsis.owners.workdesk.ownerstatus.OwnerStatus;
import ee.metsis.security.Privilege;
import spark.Request;
import spark.Response;

import java.util.Collection;

@Requestable(value = "/owner-statuses", method = RequestMethod.POST)
public class SaveOwnerStatusRequestHandler extends AbstractRequestHandler {

    private final OwnerStatusService ownerStatusService;

    public SaveOwnerStatusRequestHandler(ServiceRegistry serviceRegistry) {
        this.ownerStatusService = serviceRegistry.getOwnerStatusService();
    }

    @Override
    protected Object handleRequest(Request req, Response res) {
        OwnerStatus ownerStatus = GsonHolder.GSON.fromJson(req.body(), OwnerStatus.class);
        ownerStatusService.saveOwnerStatus(ownerStatus);
        return OkResponse.INSTANCE;
    }

    @Override
    protected Collection<String> requireAtLeastOneOfPrivileges() {
        return privileges(Privilege.ADMIN.name());
    }
}
