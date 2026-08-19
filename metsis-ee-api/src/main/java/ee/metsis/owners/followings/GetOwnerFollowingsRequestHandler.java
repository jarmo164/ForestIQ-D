package ee.metsis.owners.followings;

import ee.finenet.fineframe.http.AbstractRequestHandler;
import ee.finenet.fineframe.http.Requestable;
import ee.finenet.fineframe.user.UserMinimal;
import ee.finenet.fineframe.user.UserService;
import ee.metsis.ServiceRegistry;
import ee.metsis.owners.OwnerService;
import spark.Request;
import spark.Response;

import java.util.Collection;
import java.util.List;
import java.util.stream.Collectors;

@Requestable("/owner/:id/followings")
public class GetOwnerFollowingsRequestHandler extends AbstractRequestHandler {

    private final OwnerService ownerService;
    private final UserService userService;

    public GetOwnerFollowingsRequestHandler(ServiceRegistry serviceRegistry) {
        this.ownerService = serviceRegistry.getOwnerService();
        this.userService = serviceRegistry.getUserService();
    }

    @Override
    protected GetOwnerFollowingsResponse handleRequest(Request req, Response res) {
        String ownerId = req.params("id");
        if (ownerId == null) {
            throw new IllegalArgumentException("Can not figure out followers for null owner");
        }
        List<String> activeFollowings = ownerService.getOwnerFollowings(ownerId);
        List<String> nonFollowers =
                userService
                        .getAllUsers()
                        .stream()
                        .map(UserMinimal::getId)
                        .filter(u -> !activeFollowings.contains(u))
                        .collect(Collectors.toList());
        return new GetOwnerFollowingsResponse(activeFollowings, nonFollowers);
    }

    @Override
    protected Collection<String> requireAtLeastOneOfPrivileges() {
        return noPrivilegesRequired();
    }
}
