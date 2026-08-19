package ee.metsis.owners.cadastres.notifications;

import ee.finenet.fineframe.http.AbstractRequestHandler;
import ee.finenet.fineframe.http.Requestable;
import ee.finenet.fineframe.utilities.BooleanUtility;
import ee.metsad.register.models.ForestNotificationModel;
import ee.metsis.ServiceRegistry;
import ee.metsis.owners.OwnerService;
import ee.metsis.security.Privilege;
import spark.Request;
import spark.Response;

import java.util.Collection;
import java.util.List;

@Requestable("/cadastres/:id/notifications")
public class GetCadastreNotificationsRequestHandler extends AbstractRequestHandler {

    private final OwnerService ownerService;

    public GetCadastreNotificationsRequestHandler(ServiceRegistry serviceRegistry) {
        this.ownerService = serviceRegistry.getOwnerService();
    }

    @Override
    protected List<ForestNotificationModel> handleRequest(Request req, Response res) {
        String cadastre = req.params(":id");
        boolean refreshCashes = BooleanUtility.parseBooleanSilent(req.queryParams("refreshCaches"));
        boolean includeArchived = BooleanUtility.parseBooleanSilent(req.queryParams("includeArchived"));
        return ownerService.getCadastreNotifications(cadastre, refreshCashes, includeArchived);
    }

    @Override
    protected Collection<String> requireAtLeastOneOfPrivileges() {
        return privileges(Privilege.OWNER_PROFILE.name(), Privilege.ASSIGNED_OWNERS.name());
    }
}
