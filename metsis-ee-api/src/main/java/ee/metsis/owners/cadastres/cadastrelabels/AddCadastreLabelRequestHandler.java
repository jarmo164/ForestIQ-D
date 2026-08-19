package ee.metsis.owners.cadastres.cadastrelabels;

import ee.finenet.fineframe.http.AbstractRequestHandler;
import ee.finenet.fineframe.http.RequestMethod;
import ee.finenet.fineframe.http.Requestable;
import ee.finenet.fineframe.http.genericmodels.OkResponse;
import ee.metsis.ServiceRegistry;
import ee.metsis.owners.OwnerService;
import ee.metsis.security.LimitedPrivilegesChecks;
import ee.metsis.security.Privilege;
import spark.Request;
import spark.Response;

import java.util.Collection;

@Requestable(value = "/cadastres/:id/labels/:label", method = RequestMethod.POST)
public class AddCadastreLabelRequestHandler extends AbstractRequestHandler {

    private final OwnerService ownerService;

    public AddCadastreLabelRequestHandler(ServiceRegistry serviceRegistry) {
        this.ownerService = serviceRegistry.getOwnerService();
    }

    @Override
    protected OkResponse handleRequest(Request req, Response res) {
        LimitedPrivilegesChecks.cadastreServiceLimitedPrivilegesCheck(req, ownerService);
        ownerService.addCadastreLabel(req.params(":id"), CadastreLabel.fromString(req.params(":label")), getAuthToken(req).getUserId());
        return OkResponse.INSTANCE;
    }

    @Override
    protected Collection<String> requireAtLeastOneOfPrivileges() {
        return privileges(Privilege.OWNER_PROFILE.name(), Privilege.ASSIGNED_OWNERS.name());
    }
}
