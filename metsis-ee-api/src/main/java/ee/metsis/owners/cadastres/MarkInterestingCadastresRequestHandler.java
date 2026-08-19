package ee.metsis.owners.cadastres;

import ee.finenet.fineframe.exceptions.BadRequestException;
import ee.finenet.fineframe.http.AbstractRequestHandler;
import ee.finenet.fineframe.http.RequestMethod;
import ee.finenet.fineframe.http.Requestable;
import ee.finenet.fineframe.http.genericmodels.OkResponse;
import ee.metsis.ServiceRegistry;
import ee.metsis.owners.Owner;
import ee.metsis.owners.OwnerNotFoundException;
import ee.metsis.owners.OwnerService;
import ee.metsis.security.LimitedPrivilegesChecks;
import ee.metsis.security.Privilege;
import spark.Request;
import spark.Response;

import java.util.Collection;
import java.util.List;
import java.util.stream.Collectors;

import static ee.finenet.fineframe.serialization.GsonHolder.GSON;
import static ee.finenet.fineframe.utilities.CollectionUtility.GSON_LIST_OF_STRINGS_TYPE;

@Requestable(value = "/owners/:id/mark-cadastres", method = RequestMethod.POST)
public class MarkInterestingCadastresRequestHandler extends AbstractRequestHandler {

    private final OwnerService ownerService;

    public MarkInterestingCadastresRequestHandler(ServiceRegistry serviceRegistry) {
        this.ownerService = serviceRegistry.getOwnerService();
    }

    @Override
    protected OkResponse handleRequest(Request req, Response res) {
        LimitedPrivilegesChecks.ownerServiceLimitedPrivilegesCheck(req, ownerService);
        String ownerId = req.params(":id");
        List<String> cadastreIds = GSON.fromJson(req.body(), GSON_LIST_OF_STRINGS_TYPE);
        assertRequestValid(ownerId, cadastreIds);
        ownerService.markInterestingCadastres(ownerId, cadastreIds);
        return OkResponse.INSTANCE;
    }

    private void assertRequestValid(String ownerId, List<String> cadastreIds) {
        Owner owner = ownerService.findOwner(ownerId).orElseThrow(OwnerNotFoundException::new);
        List<String> realCadastres = owner.getCadastres().stream().map(CadastreMinimal::getId).collect(Collectors.toList());
        for (String suppliedCadastre : cadastreIds) {
            if (!realCadastres.contains(suppliedCadastre)) {
                throw new BadRequestException("MARK_CADASTRES_ONE_OF_SUPPLIED_CADASTRES_NOT_SUPPLIED_OWNERS");
            }
        }
    }

    @Override
    protected Collection<String> requireAtLeastOneOfPrivileges() {
        return privileges(Privilege.OWNER_PROFILE.name(), Privilege.ASSIGNED_OWNERS.name());
    }
}
