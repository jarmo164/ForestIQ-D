package ee.metsis.ownercadastre.api;

public class ExternalOwnerApiHistoricCadastre {
    private String cadastreNo;
    private String acquiredAt;
    private String disposessedAt;

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

    public String getDisposessedAt() {
        return disposessedAt;
    }

    public void setDisposessedAt(String disposessedAt) {
        this.disposessedAt = disposessedAt;
    }
}
