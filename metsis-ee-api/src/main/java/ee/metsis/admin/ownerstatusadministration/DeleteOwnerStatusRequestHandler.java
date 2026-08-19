package ee.metsis.admin.ownerstatusadministration;

import ee.finenet.fineframe.http.AbstractRequestHandler;
import ee.finenet.fineframe.http.RequestMethod;
import ee.finenet.fineframe.http.Requestable;
import ee.finenet.fineframe.http.genericmodels.OkResponse;
import ee.metsis.ServiceRegistry;
import ee.metsis.security.Privilege;
import spark.Request;
import spark.Response;

import java.util.Collection;

@Requestable(value = "/owner-statuses/:id", method = RequestMethod.DELETE)
public class DeleteOwnerStatusRequestHandler extends AbstractRequestHandler {

    private final OwnerStatusService ownerStatusService;

    public DeleteOwnerStatusRequestHandler(ServiceRegistry serviceRegistry) {
        this.ownerStatusService = serviceRegistry.getOwnerStatusService();
    }

    @Override
    protected Object handleRequest(Request req, Response res) {
        ownerStatusService.deleteOwnerStatus(req.params(":id"));
        return OkResponse.INSTANCE;
    }

    @Override
    protected Collection<String> requireAtLeastOneOfPrivileges() {
        return privileges(Privilege.ADMIN.name());
    }
}
