package ee.metsis.admin.userstatistics;

import ee.finenet.fineframe.http.AbstractRequestHandler;
import ee.finenet.fineframe.http.Requestable;
import ee.metsis.users.statistics.UserStatisticsService;
import ee.metsis.ServiceRegistry;
import ee.metsis.security.Privilege;
import ee.metsis.users.statistics.UserStatisticsService;
import spark.Request;
import spark.Response;

import java.util.Collection;
import java.util.List;

@Requestable("/admin/userstatistics/owner-status-change")
public class GetUserOwnerStatusChangeStatisticsRequestHandler extends AbstractRequestHandler {

    private final UserStatisticsService userStatisticsService;

    public GetUserOwnerStatusChangeStatisticsRequestHandler(ServiceRegistry serviceRegistry) {
        this.userStatisticsService = serviceRegistry.getUserStatisticsService();
    }

    @Override
    protected List<UserOwnerStatusChangeStatistics> handleRequest(Request req, Response res) {
        return userStatisticsService.getUsersOwnerStatusChangeStatistics(new GetUserOwnerStatusChangeStatisticsModel(req));
    }

    @Override
    protected Collection<String> requireAtLeastOneOfPrivileges() {
        return privileges(Privilege.ADMIN.name());
    }
}
