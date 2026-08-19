package ee.metsis.contracts;

import java.util.Date;

public class HistoricalContractInfo {
    private String id;
    private String sellers;
    private String buyer;
    private String contractNo;
    private Date created;

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getSellers() {
        return sellers;
    }

    public void setSellers(String sellers) {
        this.sellers = sellers;
    }

    public String getBuyer() {
        return buyer;
    }

    public void setBuyer(String buyer) {
        this.buyer = buyer;
    }

    public String getContractNo() {
        return contractNo;
    }

    public void setContractNo(String contractNo) {
        this.contractNo = contractNo;
    }

    public Date getCreated() {
        return created;
    }

    public void setCreated(Date created) {
        this.created = created;
    }
}
