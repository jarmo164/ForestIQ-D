package ee.metsis.owners.followings;

import ee.finenet.fineframe.http.AbstractRequestHandler;
import ee.finenet.fineframe.http.RequestMethod;
import ee.finenet.fineframe.http.Requestable;
import ee.finenet.fineframe.http.genericmodels.OkResponse;
import ee.metsis.ServiceRegistry;
import ee.metsis.owners.OwnerService;
import spark.Request;
import spark.Response;

import java.util.Collection;

@Requestable(value = "/owner/:id/followings/:userId", method = RequestMethod.DELETE)
public class RemoveFollowingRequestHandler extends AbstractRequestHandler {

    private final OwnerService ownerService;

    public RemoveFollowingRequestHandler(ServiceRegistry serviceRegistry) {
        this.ownerService = serviceRegistry.getOwnerService();
    }

    @Override
    protected OkResponse handleRequest(Request req, Response res) {
        String ownerId = req.params("id");
        String userId = req.params("userId");
        ownerService.removeFollowing(userId, ownerId);
        return OkResponse.INSTANCE;
    }

    @Override
    protected Collection<String> requireAtLeastOneOfPrivileges() {
        return noPrivilegesRequired();
    }
}
