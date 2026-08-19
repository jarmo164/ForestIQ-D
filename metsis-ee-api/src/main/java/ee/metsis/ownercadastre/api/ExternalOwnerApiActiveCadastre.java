package ee.metsis.ownercadastre.api;

public class ExternalOwnerApiActiveCadastre {
    private String cadastreNo;
    private String acquiredAt;

    public String getCadastreNo() {
        return cadastreNo;
    }

    public void setCadastreNo(String cadastreNo) {
        this.cadastreNo = cadastreNo;
    }

    public String getAcquiredAt() {
        return acquiredAt;
    }

    public void setAcquiredAt(String acquiredAt) {
        this.acquiredAt = acquiredAt;
    }
}
