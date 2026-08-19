package ee.metsis.contracts;

public class ContractIds {
    private final String contractId;
    private final String baseId;

    public ContractIds(String contractId, String baseId) {
        this.contractId = contractId;
        this.baseId = baseId;
    }

    public String getContractId() {
        return contractId;
    }

    public String getBaseId() {
        return baseId;
    }
}
