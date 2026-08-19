package ee.metsis.adminworkdesk;

import ee.finenet.fineframe.http.AbstractRequestHandler;
import ee.finenet.fineframe.http.Requestable;
import ee.metsis.ServiceRegistry;
import ee.metsis.ServiceRegistry;
import ee.metsis.owners.OwnerService;
import ee.metsis.security.Privilege;
import spark.Request;
import spark.Response;

import java.util.Collection;

@Requestable("/admin-workdesk/prepare")
public class AdminWorkdeskPreparationRequestHandler extends AbstractRequestHandler {

    private final OwnerService ownerService;

    public AdminWorkdeskPreparationRequestHandler(ServiceRegistry serviceRegistry) {
        this.ownerService = serviceRegistry.getOwnerService();
    }

    @Override
    protected AdminWorkdeskPreparationData handleRequest(Request req, Response res) {
        return ownerService.getAdminWorkdeskPreparationData();
    }

    @Override
    protected Collection<String> requireAtLeastOneOfPrivileges() {
        return privileges(Privilege.ADMIN.name());
    }

}
