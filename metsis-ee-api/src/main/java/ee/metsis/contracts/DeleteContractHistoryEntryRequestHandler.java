package ee.metsis.contracts;

import ee.finenet.fineframe.http.AbstractRequestHandler;
import ee.finenet.fineframe.http.RequestMethod;
import ee.finenet.fineframe.http.Requestable;
import ee.finenet.fineframe.http.genericmodels.OkResponse;
import ee.metsis.ServiceRegistry;
import ee.metsis.security.Privilege;
import spark.Request;
import spark.Response;

import java.util.Collection;

@Requestable(value = "/contract/:id", method = RequestMethod.DELETE)
public class DeleteContractHistoryEntryRequestHandler extends AbstractRequestHandler {

    private final ContractService contractService;

    public DeleteContractHistoryEntryRequestHandler(ServiceRegistry serviceRegistry) {
        this.contractService = serviceRegistry.getContractService();
    }

    @Override
    protected Object handleRequest(Request req, Response res) {
        contractService.deleteContract(req.params(":id"));
        return OkResponse.INSTANCE;
    }

    @Override
    protected Collection<String> requireAtLeastOneOfPrivileges() {
        return privileges(Privilege.ADMIN.name());
    }
}
