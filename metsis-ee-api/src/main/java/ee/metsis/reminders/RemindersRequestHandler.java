package ee.metsis.reminders;

import ee.finenet.fineframe.http.AbstractRequestHandler;
import ee.finenet.fineframe.http.Requestable;
import ee.metsis.ServiceRegistry;
import ee.metsis.security.Privilege;
import spark.Request;
import spark.Response;

import java.util.Collection;

@Requestable("/reminders")
public class RemindersRequestHandler extends AbstractRequestHandler {

    private final RemindersService remindersService;

    public RemindersRequestHandler(ServiceRegistry serviceRegistry) {
        this.remindersService = serviceRegistry.getRemindersService();
    }


    @Override
    protected Object handleRequest(Request req, Response res) {
        return remindersService.getReminders(getAuthenticatedUsersId(req));
    }

    @Override
    protected Collection<String> requireAtLeastOneOfPrivileges() {
        return privileges(Privilege.OWNER_PROFILE.name(), Privilege.ASSIGNED_OWNERS.name());
    }

}
