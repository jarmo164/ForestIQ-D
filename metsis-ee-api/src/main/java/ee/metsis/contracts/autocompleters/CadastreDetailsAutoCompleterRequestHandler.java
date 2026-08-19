package ee.metsis.contracts.autocompleters;

import ee.finenet.fineframe.http.AbstractRequestHandler;
import ee.finenet.fineframe.http.Requestable;
import ee.metsis.ServiceRegistry;
import ee.metsis.security.Privilege;
import spark.Request;
import spark.Response;

import java.util.Collection;

@Requestable("/autocompleters/cadastre-details/:id")
public class CadastreDetailsAutoCompleterRequestHandler extends AbstractRequestHandler {

    private final AutoCompleterService autoCompleterService;

    public CadastreDetailsAutoCompleterRequestHandler(ServiceRegistry serviceRegistry) {
        this.autoCompleterService = serviceRegistry.getAutoCompleterService();
    }

    @Override
    protected Object handleRequest(Request req, Response res) {
        return autoCompleterService.getCadastreDetails(req.params(":id"));
    }

    @Override
    protected Collection<String> requireAtLeastOneOfPrivileges() {
        return privileges(Privilege.ADMIN.name());
    }
}
