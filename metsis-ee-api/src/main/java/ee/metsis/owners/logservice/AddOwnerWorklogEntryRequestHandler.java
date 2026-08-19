package ee.metsis.owners.logservice;

import ee.finenet.fineframe.exceptions.BadRequestException;
import ee.finenet.fineframe.exceptions.ResourceNotFoundException;
import ee.finenet.fineframe.http.AbstractRequestHandler;
import ee.finenet.fineframe.http.RequestMethod;
import ee.finenet.fineframe.http.Requestable;
import ee.finenet.fineframe.user.UserMinimal;
import ee.finenet.fineframe.utilities.StringUtility;
import ee.metsis.ServiceRegistry;
import ee.metsis.owners.Owner;
import ee.metsis.owners.OwnerMinimal;
import ee.metsis.owners.OwnerService;
import ee.metsis.security.LimitedPrivilegesChecks;
import ee.metsis.security.Privilege;
import spark.Request;
import spark.Response;

import java.util.Collection;
import java.util.List;

import static ee.finenet.fineframe.serialization.GsonHolder.GSON;

@Requestable(value = "/owners/:id/log", method = RequestMethod.POST)
public class AddOwnerWorklogEntryRequestHandler extends AbstractRequestHandler {

    private final OwnerLogService ownerLogService;
    private final OwnerService ownerService;

    public AddOwnerWorklogEntryRequestHandler(ServiceRegistry serviceRegistry) {
        this.ownerLogService = serviceRegistry.getOwnerLogService();
        this.ownerService = serviceRegistry.getOwnerService();
    }

    @Override
    protected List<LogMessage> handleRequest(Request req, Response res) {
        LimitedPrivilegesChecks.ownerServiceLimitedPrivilegesCheck(req, ownerService);
        String ownerId = req.params(":id");
        AddOwnerWorklogEntryModel reqModel = GSON.fromJson(req.body(), AddOwnerWorklogEntryModel.class);
        String message = StringUtility.emptyIfNull(reqModel.getMessage()).trim();
        if (message.isEmpty()) {
            throw new BadRequestException("EMPTY_LOG_MESSGE_NOT_ALLOWED");
        }
        LogMessage logMessage = new LogMessage();
        logMessage.setMessage(message);
        logMessage.setOwner(ownerId);
        String loggedInUserId = getAuthToken(req).getUserId();
        logMessage.setCreator(loggedInUserId);
        logMessage.setOwnersAssignee(ownerService.findOwner(ownerId).map(OwnerMinimal::getAssignee).map(UserMinimal::getId).orElse(null));
        Long createdLogLineId = ownerLogService.writeLog(logMessage);
        String ownerName = ownerService.findOwner(ownerId).map(Owner::getName)
                .orElseThrow(() -> new ResourceNotFoundException("OWNER_NOT_FOUND"));
        ownerService.sendMessageToEachOwnerFollowerExcept(ownerId, String.format("Added comment to owner %s (%s): '%s'.",
                ownerName, ownerId, message), loggedInUserId, loggedInUserId);
        return ownerLogService.getOwnersWorkLog(ownerId, createdLogLineId);
    }

    @Override
    protected Collection<String> requireAtLeastOneOfPrivileges() {
        return privileges(Privilege.OWNER_PROFILE.name(), Privilege.ASSIGNED_OWNERS.name());
    }
}
