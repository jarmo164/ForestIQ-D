package ee.metsis.owners.cadastres.registryfeatures;

import ee.finenet.fineframe.http.AbstractRequestHandler;
import ee.finenet.fineframe.http.Requestable;
import ee.metsis.ServiceRegistry;
import ee.metsis.owners.OwnerService;
import ee.metsis.security.LimitedPrivilegesChecks;
import ee.metsis.security.Privilege;
import spark.Request;
import spark.Response;

import java.util.Collection;
import java.util.List;

@Requestable("/cadastres/:id/registry-features")
public class GetForestRegistryFeaturesRequestHandler extends AbstractRequestHandler {

    private final OwnerService ownerService;

    public GetForestRegistryFeaturesRequestHandler(ServiceRegistry serviceRegistry) {
        this.ownerService = serviceRegistry.getOwnerService();
    }

    @Override
    protected List<ForestRegistryFeature> handleRequest(Request req, Response res) {
        LimitedPrivilegesChecks.cadastreServiceLimitedPrivilegesCheck(req, ownerService);
        return ownerService.getForestRegistryFeatures(req.params(":id"));
    }

    @Override
    protected Collection<String> requireAtLeastOneOfPrivileges() {
        return privileges(Privilege.OWNER_PROFILE.name(), Privilege.ASSIGNED_OWNERS.name());
    }
}
