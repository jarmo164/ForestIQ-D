package ee.metsis.contracts.autocompleters;

import ee.finenet.fineframe.http.AbstractRequestHandler;
import ee.finenet.fineframe.http.Requestable;
import ee.metsis.ServiceRegistry;
import ee.metsis.contracts.ContractParty;
import ee.metsis.security.Privilege;
import spark.Request;
import spark.Response;

import java.util.Collection;

@Requestable("/autocompleters/owner-details/:id")
public class OwnerDetailsAutoCompleterRequestHandler extends AbstractRequestHandler {

    private final AutoCompleterService autoCompleterService;

    public OwnerDetailsAutoCompleterRequestHandler(ServiceRegistry serviceRegistry) {
        this.autoCompleterService = serviceRegistry.getAutoCompleterService();
    }

    @Override
    protected ContractParty handleRequest(Request req, Response res) {
        return autoCompleterService.getOwnersDetails(req.params(":id"));
    }

    @Override
    protected Collection<String> requireAtLeastOneOfPrivileges() {
        return privileges(Privilege.ADMIN.name());
    }
}
