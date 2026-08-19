package ee.metsis.owners;

import ee.finenet.fineframe.exceptions.BadRequestException;
import ee.finenet.fineframe.http.AbstractRequestHandler;
import ee.finenet.fineframe.http.RequestMethod;
import ee.finenet.fineframe.http.Requestable;
import ee.finenet.fineframe.http.genericmodels.OkResponse;
import ee.finenet.fineframe.serialization.GsonHolder;
import ee.finenet.fineframe.utilities.NumbersUtility;
import ee.finenet.fineframe.utilities.StringUtility;
import ee.metsis.ServiceRegistry;
import ee.metsis.security.Privilege;
import spark.Request;
import spark.Response;

import java.util.Collection;

@Requestable(value = "/owners/:id/add", method = RequestMethod.POST)
public class AddNewOwnerRequestHandler extends AbstractRequestHandler {

    private final OwnerService ownerService;

    public AddNewOwnerRequestHandler(ServiceRegistry serviceRegistry) {
        this.ownerService = serviceRegistry.getOwnerService();
    }

    @Override
    protected Object handleRequest(Request req, Response res) {
        String ownerId = req.params(":id");
        AddNewOwnerModel addNewOwnerModel = GsonHolder.GSON.fromJson(req.body(), AddNewOwnerModel.class);
        String ownerName = StringUtility.trimToNull(addNewOwnerModel.getOwnerName());
        if (ownerName == null) {
            throw new BadRequestException("ADD_OWNER_BLANK_OWNER_NAME_NOT_ALLOWED");
        }
        if (ownerName.length() > 100) {
            throw new BadRequestException("ADD_OWNER_OWNER_NAME_TOO_LONG");
        }
        if (ownerId.length() > 50) {
            throw new BadRequestException("ADD_OWNER_OWNER_ID_TOO_LONG");
        }
        if (NumbersUtility.parseLongSilent(ownerId) == null) {
            throw new BadRequestException("ADD_OWNER_ONLY_NUMBERS_ALLOWED");
        }
        ownerService.addNewOwner(ownerId, ownerName, addNewOwnerModel.getOwnerType(), getAuthenticatedUsersId(req));
        return OkResponse.INSTANCE;
    }

    @Override
    protected Collection<String> requireAtLeastOneOfPrivileges() {
        return privileges(Privilege.OWNER_PROFILE.name());
    }

}
