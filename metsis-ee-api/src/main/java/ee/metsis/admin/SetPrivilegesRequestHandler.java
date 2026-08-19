package ee.metsis.admin;

import ee.finenet.fineframe.http.AbstractRequestHandler;
import ee.finenet.fineframe.http.RequestMethod;
import ee.finenet.fineframe.http.Requestable;
import ee.finenet.fineframe.http.genericmodels.OkResponse;
import ee.finenet.fineframe.user.UserService;
import ee.finenet.fineframe.utilities.CollectionUtility;
import ee.metsis.ServiceRegistry;
import ee.metsis.security.Privilege;
import spark.Request;
import spark.Response;

import java.util.Collection;
import java.util.List;
import java.util.Objects;
import java.util.stream.Collectors;

import static ee.finenet.fineframe.serialization.GsonHolder.GSON;

@Requestable(value = "/admin/users/:user", method = RequestMethod.POST)
public class SetPrivilegesRequestHandler extends AbstractRequestHandler {

    private final UserService userService;

    public SetPrivilegesRequestHandler(ServiceRegistry serviceRegistry) {
        this.userService = serviceRegistry.getUserService();
    }

    @Override
    public OkResponse handleRequest(Request req, Response res) {
        String userId = req.params(":user");
        List<Privilege> givenPrivileges = GSON.fromJson(req.body(), Privilege.GSON_LIST_TYPE);
        List<Privilege> sanitizedGivenPrivileges = CollectionUtility.emptyIfNull(givenPrivileges);
        sanitizedGivenPrivileges = sanitizedGivenPrivileges.stream().filter(Objects::nonNull).collect(Collectors.toList());
        userService.setUserPrivileges(userId, sanitizedGivenPrivileges.stream().map(Privilege::name).collect(Collectors.toList()));
        return OkResponse.INSTANCE;
    }

    @Override
    protected Collection<String> requireAtLeastOneOfPrivileges() {
        return privileges(Privilege.ADMIN.name());
    }

}
