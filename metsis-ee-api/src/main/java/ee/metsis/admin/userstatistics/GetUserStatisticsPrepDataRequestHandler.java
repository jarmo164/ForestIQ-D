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

@Requestable("/admin/userstatistics/prep-data")
public class GetUserStatisticsPrepDataRequestHandler extends AbstractRequestHandler {

    private final UserStatisticsService userStatisticsService;

    public GetUserStatisticsPrepDataRequestHandler(ServiceRegistry serviceRegistry) {
        this.userStatisticsService = serviceRegistry.getUserStatisticsService();
    }

    @Override
    protected UserStatisticsPrepData handleRequest(Request req, Response res) {
        return userStatisticsService.getPrepData();
    }

    @Override
    protected Collection<String> requireAtLeastOneOfPrivileges() {
        return privileges(Privilege.ADMIN.name());
    }
}
