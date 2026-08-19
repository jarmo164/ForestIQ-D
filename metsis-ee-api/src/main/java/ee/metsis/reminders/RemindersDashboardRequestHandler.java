package ee.metsis.reminders;

import ee.finenet.fineframe.http.AbstractRequestHandler;
import ee.finenet.fineframe.http.Requestable;
import ee.metsis.ServiceRegistry;
import ee.metsis.security.Privilege;
import spark.Request;
import spark.Response;

import java.util.Collection;

import static ee.finenet.fineframe.utilities.CollectionUtility.commaSepparatedStringToList;

@Requestable("/reminders-dashboard")
public class RemindersDashboardRequestHandler extends AbstractRequestHandler {

    private final RemindersService remindersService;

    public RemindersDashboardRequestHandler(ServiceRegistry serviceRegistry) {
        this.remindersService = serviceRegistry.getRemindersService();
    }


    @Override
    protected Object handleRequest(Request req, Response res) {
        return remindersService.getFutureReminders(
                commaSepparatedStringToList(
                        req.queryParams("creators")
                )
        );
    }

    @Override
    protected Collection<String> requireAtLeastOneOfPrivileges() {
        return privileges(Privilege.ADMIN.name());
    }

}
