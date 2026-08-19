package ee.metsis.owners.cadastres;

import ee.finenet.fineframe.http.AbstractRequestHandler;
import ee.finenet.fineframe.http.Requestable;
import ee.finenet.fineframe.utilities.BooleanUtility;
import ee.metsis.ServiceRegistry;
import ee.metsis.owners.OwnerService;
import ee.metsis.security.Privilege;
import spark.Request;
import spark.Response;

import java.util.Collection;

@Requestable("/cadastres/:id/areas")
public class AreasRequestHandler extends AbstractRequestHandler {

    private final OwnerService ownerService;

    public AreasRequestHandler(ServiceRegistry serviceRegistry) {
        this.ownerService = serviceRegistry.getOwnerService();
    }

    @Override
    protected Areas handleRequest(Request req, Response res) {
        String cadastre = req.params(":id");
        boolean refreshCaches = BooleanUtility.parseBooleanSilent(req.queryParams("refreshCaches"));
        return this.ownerService.getCadastreAreas(cadastre, refreshCaches);
    }

    @Override
    protected Collection<String> requireAtLeastOneOfPrivileges() {
        return privileges(Privilege.OWNER_PROFILE.name(), Privilege.ASSIGNED_OWNERS.name());
    }
}
