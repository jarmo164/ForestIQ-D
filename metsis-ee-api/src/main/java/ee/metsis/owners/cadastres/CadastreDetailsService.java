package ee.metsis.owners.cadastres;

import ee.finenet.fineframe.http.AbstractRequestHandler;
import ee.finenet.fineframe.http.Requestable;
import ee.metsis.ServiceRegistry;
import ee.metsis.owners.OwnerService;
import ee.metsis.security.LimitedPrivilegesChecks;
import ee.metsis.security.Privilege;
import spark.Request;
import spark.Response;

import java.util.Collection;

@Requestable("/cadastres/:id")
public class CadastreDetailsService extends AbstractRequestHandler {

    private final OwnerService ownerService;

    public CadastreDetailsService(ServiceRegistry serviceRegistry) {
        this.ownerService = serviceRegistry.getOwnerService();
    }

    @Override
    protected Cadastre handleRequest(Request req, Response res) {
        LimitedPrivilegesChecks.cadastreServiceLimitedPrivilegesCheck(req, ownerService);
        return ownerService.findCadastre(req.params(":id")).orElseThrow(CadastreNotFoundException::new);
    }

    @Override
    protected Collection<String> requireAtLeastOneOfPrivileges() {
        return privileges(Privilege.OWNER_PROFILE.name(), Privilege.ASSIGNED_OWNERS.name());
    }
}
