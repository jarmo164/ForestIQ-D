package ee.metsis.sharedmodels;

import java.util.List;

public class OwnerWithCadastres {
    private String ownerId;
    private List<String> cadastres;

    public String getOwnerId() {
        return ownerId;
    }

    public void setOwnerId(String ownerId) {
        this.ownerId = ownerId;
    }

    public List<String> getCadastres() {
        return cadastres;
    }

    public void setCadastres(List<String> cadastres) {
        this.cadastres = cadastres;
    }
}
