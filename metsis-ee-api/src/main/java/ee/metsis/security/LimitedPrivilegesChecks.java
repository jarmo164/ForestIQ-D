package ee.metsis.security;

import ee.finenet.fineframe.exceptions.UnexpextedException;
import ee.finenet.fineframe.security.token.AuthToken;
import ee.finenet.fineframe.user.UserMinimal;
import ee.metsis.owners.cadastres.CadastreNotFoundException;
import ee.metsis.owners.OwnerMinimal;
import ee.metsis.owners.OwnerNotFoundException;
import ee.metsis.owners.OwnerService;
import spark.Request;

import static ee.metsis.security.token.AuthTokenValidationFilter.ATTR_AUTH_TOKEN;

public class LimitedPrivilegesChecks {

    public static void cadastreServiceLimitedPrivilegesCheck(Request req, OwnerService ownerService) {
        String cadastreId = req.params(":id");
        if (authenticatedUserHasLimitedOwnerPrivileges(req)) {
            String authenticatedUsersId = getAuthenticatedUsersId(req);
            long countOfAssigneesCadastres = ownerService.findCadastre(cadastreId).orElseThrow(CadastreNotFoundException::new)
                    .getOwners().stream().map(OwnerMinimal::getAssignee).map(UserMinimal::getId)
                    .map(authenticatedUsersId::equals).count();
            if (countOfAssigneesCadastres == 0) {
                throw new CadastreNotFoundException();
            }
        }
    }

    public static  void ownerServiceLimitedPrivilegesCheck(Request req, OwnerService ownerService) {
        String ownerId = req.params(":id");
        if (authenticatedUserHasLimitedOwnerPrivileges(req)) {
            if (!getAuthToken(req).getUserId().equals(ownerService.findOwner(ownerId).orElseThrow(OwnerNotFoundException::new).getAssignee().getId())) {
                throw new OwnerNotFoundException();
            }
        }
    }

    public static  boolean authenticatedUserHasLimitedOwnerPrivileges(Request req) {
        return !getAuthToken(req).getPrivileges().contains(Privilege.OWNER_PROFILE.name());
    }

    public static String getAuthenticatedUsersId(Request req) {
        return getAuthToken(req).getUserId();
    }

    public static AuthToken getAuthToken(Request req) {
        AuthToken authToken = req.attribute(ATTR_AUTH_TOKEN);
        if (authToken == null) {
            throw new UnexpextedException("Somehow user got past the auth filter and yet the auth token is not set as request attribute. This should not be possible");
        }
        return authToken;
    }

    public static String getLoggedInUser(Request req) {
        AuthToken authToken = req.attribute(ATTR_AUTH_TOKEN);
        if (authToken == null) {
            return null;
        }
        return authToken.getUserId();
    }
}
