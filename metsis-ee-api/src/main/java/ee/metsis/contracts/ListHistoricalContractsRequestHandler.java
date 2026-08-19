package ee.metsis.contracts;

import ee.finenet.fineframe.http.AbstractRequestHandler;
import ee.finenet.fineframe.http.Requestable;
import ee.metsis.ServiceRegistry;
import ee.metsis.security.Privilege;
import spark.Request;
import spark.Response;

import java.util.Collection;

@Requestable("/contracts/history")
public class ListHistoricalContractsRequestHandler extends AbstractRequestHandler {

    private final ContractService contractService;

    public ListHistoricalContractsRequestHandler(ServiceRegistry serviceRegistry) {
        this.contractService = serviceRegistry.getContractService();
    }

    @Override
    protected Object handleRequest(Request req, Response res) {
        return contractService.getHistory(new HistoricalContractSearchFilter(req));
    }

    @Override
    protected Collection<String> requireAtLeastOneOfPrivileges() {
        return privileges(Privilege.ADMIN.name());
    }
}
