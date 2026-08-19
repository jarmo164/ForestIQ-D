package ee.metsis.owners;

import ee.finenet.fineframe.exceptions.BadRequestException;
import ee.finenet.fineframe.http.AbstractRequestHandler;
import ee.finenet.fineframe.http.RequestMethod;
import ee.finenet.fineframe.http.Requestable;
import ee.finenet.fineframe.http.genericmodels.OkResponse;
import ee.finenet.fineframe.utilities.StringUtility;
import ee.metsis.ServiceRegistry;
import ee.metsis.security.LimitedPrivilegesChecks;
import ee.metsis.security.Privilege;
import spark.Request;
import spark.Response;

import java.util.Collection;

import static ee.finenet.fineframe.serialization.GsonHolder.GSON;

@Requestable(value = "/owners/:id", method = RequestMethod.POST)
public class SaveOwnerChangesRequestHandler extends AbstractRequestHandler {

    private final OwnerService ownerService;

    public SaveOwnerChangesRequestHandler(ServiceRegistry serviceRegistry) {
        this.ownerService = serviceRegistry.getOwnerService();
    }

    @Override
    protected OkResponse handleRequest(Request req, Response res) {
        LimitedPrivilegesChecks.ownerServiceLimitedPrivilegesCheck(req, ownerService);
        String id = req.params(":id");
        String body = req.body();
        Owner owner = GSON.fromJson(body, Owner.class);
        owner.setId(id);
        assertRequestValid(owner);
        ownerService.saveOwnerChanges(owner);
        String ownerId = owner.getId();
        String loggedInUsersId = getAuthToken(req).getUserId();
        ownerService.sendMessageToEachOwnerFollowerExcept(ownerId,
                "Owner details changed for owner " + owner.getName() + " (" + ownerId + ")",
                loggedInUsersId,
                loggedInUsersId);
        return OkResponse.INSTANCE;
    }

    private void assertRequestValid(Owner owner) {
        if (StringUtility.isNullOrBlank(owner.getName())) {
            throw new BadRequestException("OWNER_NAME_EMPTY");
        }
        if (owner.getName().length() > 100) {
            throw new BadRequestException("OWNER_NAME_TOO_LONG");
        }
        if (StringUtility.emptyIfNull(owner.getPhone()).length() > 100) {
            throw new BadRequestException("OWNER_PHONE_TOO_LONG");
        }
        if (StringUtility.emptyIfNull(owner.getEmail()).length() > 100) {
            throw new BadRequestException("OWNER_EMAIL_TOO_LONG");
        }
        if (StringUtility.emptyIfNull(owner.getType()).length() > 20) {
            throw new BadRequestException("OWNER_TYPE_TOO_LONG");
        }
        if (StringUtility.emptyIfNull(owner.getAddress()).length() > 500) {
            throw new BadRequestException("OWNER_ADDRESS_TOO_LONG");
        }
    }

    @Override
    protected Collection<String> requireAtLeastOneOfPrivileges() {
        return privileges(Privilege.OWNER_PROFILE.name(), Privilege.ASSIGNED_OWNERS.name());
    }
}
