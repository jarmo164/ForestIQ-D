package ee.metsis.reminders;

import ee.finenet.fineframe.http.AbstractRequestHandler;
import ee.finenet.fineframe.http.RequestMethod;
import ee.finenet.fineframe.http.Requestable;
import ee.finenet.fineframe.http.genericmodels.OkResponse;
import ee.finenet.fineframe.serialization.GsonHolder;
import ee.metsis.ServiceRegistry;
import ee.metsis.security.Privilege;
import spark.Request;
import spark.Response;

import java.util.Collection;

@Requestable(value = "/reminders", method = RequestMethod.POST)
public class AddReminderRequestHandler extends AbstractRequestHandler {

    private final RemindersService remindersService;

    public AddReminderRequestHandler(ServiceRegistry serviceRegistry) {
        this.remindersService = serviceRegistry.getRemindersService();
    }

    @Override
    protected Object handleRequest(Request req, Response res) {
        remindersService.addReminder(GsonHolder.GSON.fromJson(req.body(), Reminder.class), getAuthenticatedUsersId(req));
        return OkResponse.INSTANCE;
    }

    @Override
    protected Collection<String> requireAtLeastOneOfPrivileges() {
        return privileges(Privilege.OWNER_PROFILE.name(), Privilege.ASSIGNED_OWNERS.name());
    }
}
