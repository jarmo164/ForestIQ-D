package ee.metsis.contracts;

import java.util.List;

public class ContractData {
    private String contractNumber;
    private BuyerParty buyer;
    private List<SellerParty> sellers;
    private ContractDetails contractDetails;
    private Integer templateNumber;

    public static final int TEMPLATE1 = 0;
    public static final int TEMPLATE2 = 1;

    public String getContractNumber() {
        return contractNumber;
    }

    public void setContractNumber(String contractNumber) {
        this.contractNumber = contractNumber;
    }

    public BuyerParty getBuyer() {
        return buyer;
    }

    public void setBuyer(BuyerParty buyer) {
        this.buyer = buyer;
    }

    public List<SellerParty> getSellers() {
        return sellers;
    }

    public void setSellers(List<SellerParty> sellers) {
        this.sellers = sellers;
    }

    public ContractDetails getContractDetails() {
        return contractDetails;
    }

    public void setContractDetails(ContractDetails contractDetails) {
        this.contractDetails = contractDetails;
    }

    public int getTemplateNumber() {
        return templateNumber;
    }

    public void setTemplateNumber(Integer templateNumber) {
        this.templateNumber = templateNumber;
    }
}
