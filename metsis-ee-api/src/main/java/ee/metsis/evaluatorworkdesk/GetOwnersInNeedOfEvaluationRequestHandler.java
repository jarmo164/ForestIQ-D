package ee.metsis.evaluatorworkdesk;

import ee.finenet.fineframe.http.AbstractRequestHandler;
import ee.finenet.fineframe.http.Requestable;
import ee.metsis.ServiceRegistry;
import ee.metsis.ServiceRegistry;
import ee.metsis.owners.OwnerMinimal;
import ee.metsis.owners.OwnerService;
import ee.metsis.security.Privilege;
import spark.Request;
import spark.Response;

import java.util.Collection;
import java.util.List;

@Requestable("/owners-in-need-of-evaluation")
public class GetOwnersInNeedOfEvaluationRequestHandler extends AbstractRequestHandler {

    private final OwnerService ownerService;

    public GetOwnersInNeedOfEvaluationRequestHandler(ServiceRegistry serviceRegistry) {
        this.ownerService = serviceRegistry.getOwnerService();
    }

    @Override
    protected List<OwnerMinimal> handleRequest(Request req, Response res) {
        return ownerService.getOwnersInNeedOfEvaluation();
    }

    @Override
    protected Collection<String> requireAtLeastOneOfPrivileges() {
        return privileges(Privilege.EVALUATION.name());
    }
}
