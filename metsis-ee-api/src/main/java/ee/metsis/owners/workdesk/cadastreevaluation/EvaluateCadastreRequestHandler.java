package ee.metsis.owners.workdesk.cadastreevaluation;

import ee.finenet.fineframe.http.AbstractRequestHandler;
import ee.finenet.fineframe.http.RequestMethod;
import ee.finenet.fineframe.http.Requestable;
import ee.finenet.fineframe.http.genericmodels.OkResponse;
import ee.metsis.ServiceRegistry;
import ee.metsis.owners.OwnerService;
import ee.metsis.owners.cadastres.CadastreNotFoundException;
import ee.metsis.security.LimitedPrivilegesChecks;
import ee.metsis.security.Privilege;
import spark.Request;
import spark.Response;

import java.util.Collection;

import static ee.finenet.fineframe.serialization.GsonHolder.GSON;

@Requestable(value = "/cadastres/:id/evaluation", method = RequestMethod.POST)
public class EvaluateCadastreRequestHandler extends AbstractRequestHandler {

    private final OwnerService ownerService;

    public EvaluateCadastreRequestHandler(ServiceRegistry serviceRegistry) {
        this.ownerService = serviceRegistry.getOwnerService();
    }

    @Override
    protected OkResponse handleRequest(Request req, Response res) {
        LimitedPrivilegesChecks.cadastreServiceLimitedPrivilegesCheck(req, ownerService);
        String cadastreNo = req.params(":id");
        CadastreEvaluation evaluation = GSON.fromJson(req.body(), CadastreEvaluation.class);
        assertRequestValid(cadastreNo);
        ownerService.saveCadastreEvaluation(cadastreNo, evaluation, getAuthToken(req).getUserId());
        return OkResponse.INSTANCE;
    }

    private void assertRequestValid(String cadastreNo) {
        ownerService.getCadastreEvaluation(cadastreNo).orElseThrow(CadastreNotFoundException::new);
    }

    @Override
    protected Collection<String> requireAtLeastOneOfPrivileges() {
        return privileges(Privilege.OWNER_PROFILE.name(), Privilege.ASSIGNED_OWNERS.name());
    }
}
