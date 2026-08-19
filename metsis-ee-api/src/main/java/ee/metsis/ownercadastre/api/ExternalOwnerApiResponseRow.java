package ee.metsis.ownercadastre.api;

import java.util.List;

public class ExternalOwnerApiResponseRow {
    private ExternalOwnerApiOwner owner;
    private List<ExternalOwnerApiActiveCadastre> activeOwnings;
    private List<ExternalOwnerApiHistoricCadastre> historicOwnings;

    public ExternalOwnerApiOwner getOwner() {
        return owner;
    }

    public void setOwner(ExternalOwnerApiOwner owner) {
        this.owner = owner;
    }

    public List<ExternalOwnerApiActiveCadastre> getActiveOwnings() {
        return activeOwnings;
    }

    public void setActiveOwnings(List<ExternalOwnerApiActiveCadastre> activeOwnings) {
        this.activeOwnings = activeOwnings;
    }

    public List<ExternalOwnerApiHistoricCadastre> getHistoricOwnings() {
        return historicOwnings;
    }

    public void setHistoricOwnings(List<ExternalOwnerApiHistoricCadastre> historicOwnings) {
        this.historicOwnings = historicOwnings;
    }
}
