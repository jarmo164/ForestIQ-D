package ee.metsis.contracts;

import ee.finenet.fineframe.exceptions.UnexpextedException;
import ee.finenet.fineframe.http.RequestHandler;
import ee.finenet.fineframe.http.Requestable;
import ee.metsis.ServiceRegistry;
import spark.Request;
import spark.Response;

import java.io.IOException;
import java.util.Optional;

import static ee.metsis.contracts.ContractData.TEMPLATE1;

@Requestable(value = "/contract/:id/:baseId", secured = false)
public class GetCreatedContractRequestHandler implements RequestHandler {
    private final ContractService contractService;

    public GetCreatedContractRequestHandler(ServiceRegistry serviceRegistry) {
        contractService = serviceRegistry.getContractService();
    }

    @Override
    public byte[] handle(Request req, Response res) {
        String id = req.params(":id");
        String baseId = req.params(":baseId");
        Optional<ContractData> contractBase = contractService.getContractBase(baseId);
        Boolean isTmEnergy = contractBase.map(ContractData::getBuyer).map(it -> it.getCode().equals("10828349")).orElse(false);
        Optional<Integer> templateNo = contractBase.map(ContractData::getTemplateNumber);
        String contentType = templateNo.orElse(TEMPLATE1) == TEMPLATE1 || !isTmEnergy
                ? "application/pdf"
                : "application/vnd.openxmlformats-officedocument.wordprocessingml.document";
        String extension = contentType.equals("application/pdf") ? "pdf" : "docx";
        res.raw().setContentType(contentType);
        res.raw().setHeader("Content-Disposition","attachment; filename=contract" + id + "." + extension);
        byte[] createdContract = contractService.getCreatedContract(id);
        try {
            res.raw().getOutputStream().write(createdContract);
        } catch (IOException e) {
            throw new UnexpextedException("Downloading contract " + id + " failed", e);
        }
        return null;
    }

}
