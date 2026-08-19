package ee.metsis.contracts;

import ee.finenet.fineframe.http.AbstractRequestHandler;
import ee.finenet.fineframe.http.RequestMethod;
import ee.finenet.fineframe.http.Requestable;
import ee.finenet.fineframe.serialization.GsonHolder;
import ee.metsis.ServiceRegistry;
import ee.metsis.security.Privilege;
import spark.Request;
import spark.Response;

import java.util.Collection;

@Requestable(value = "/contract", method = RequestMethod.POST)
public class CreateContractRequestHandler extends AbstractRequestHandler {

    private final ContractService contractService;

    public CreateContractRequestHandler(ServiceRegistry serviceRegistry) {
        this.contractService = serviceRegistry.getContractService();
    }

    @Override
    protected CreatedContractInfo handleRequest(Request req, Response res) {
        ContractIds contractIds = contractService.generate(GsonHolder.GSON.fromJson(req.body(), ContractData.class));
        String path = contractIds.getContractId();
        CreatedContractInfo createdContractInfo = new CreatedContractInfo();
        createdContractInfo.setPath("/api/contract/" + path);
        createdContractInfo.setBaseId(contractIds.getBaseId());
        return createdContractInfo;
    }

    @Override
    protected Collection<String> requireAtLeastOneOfPrivileges() {
        return privileges(Privilege.ADMIN.name());
    }
}
