package ee.finenet.fineframe.http;

import ee.finenet.fineframe.exceptions.ForbiddenException;
import ee.finenet.fineframe.exceptions.UnexpextedException;
import ee.finenet.fineframe.security.token.AuthToken;
import spark.Request;
import spark.Response;

import java.util.Arrays;
import java.util.Collection;
import java.util.Collections;
import java.util.List;

import static ee.finenet.fineframe.exceptions.ForbiddenException.CODE_NOT_ENOUGH_PRIVILEGES;
import static ee.finenet.fineframe.security.token.AuthTokenValidationFilter.ATTR_AUTH_TOKEN;

public abstract class AbstractRequestHandler implements RequestHandler {

    @Override
    public Object handle(Request req, Response res) {
        AuthToken authToken = getAuthToken(req);
        List<String> existingPrivileges = authToken.getPrivileges();
        Collection<String> requiredPrivileges = requireAtLeastOneOfPrivileges();
        boolean hasEnoughPrivileges = requiredPrivileges.isEmpty();
        for (String requiredPrivilege : requiredPrivileges) {
            if (existingPrivileges.contains(requiredPrivilege)) {
                hasEnoughPrivileges = true;
                break;
            }
        }
        if (!hasEnoughPrivileges) {
            throw new ForbiddenException(CODE_NOT_ENOUGH_PRIVILEGES);
        }
        return handleRequest(req, res);
    }

    protected AuthToken getAuthToken(Request req) {
        AuthToken authToken = req.attribute(ATTR_AUTH_TOKEN);
        if (authToken == null) {
            throw new UnexpextedException("Somehow user got past the auth filter and yet the auth token is not set as request attribute. This should not be possible");
        }
        return authToken;
    }

    protected String getAuthenticatedUsersId(Request req) {
        return getAuthToken(req).getUserId();
    }

    protected abstract Object handleRequest(Request req, Response res);

    protected abstract Collection<String> requireAtLeastOneOfPrivileges();

    protected Collection<String> privileges(String ... privileges) {
        return Arrays.asList(privileges);
    }

    protected Collection<String> noPrivilegesRequired() {
        return Collections.emptyList();
    }


}
