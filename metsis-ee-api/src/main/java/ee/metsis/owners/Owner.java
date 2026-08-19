package ee.metsis.owners;

import ee.metsis.owners.cadastres.CadastreMinimal;

import java.util.List;

public class Owner extends OwnerMinimal {

    private String type;
    private String email;
    private String address;
    private String info;
    private List<CadastreMinimal> cadastres;
    private Long lastCadastreListRefresh;

    public String getType() {
        return type;
    }

    public void setType(String type) {
        this.type = type;
    }

    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }

    public String getAddress() {
        return address;
    }

    public void setAddress(String address) {
        this.address = address;
    }

    public String getInfo() {
        return info;
    }

    public void setInfo(String info) {
        this.info = info;
    }

    public List<CadastreMinimal> getCadastres() {
        return cadastres;
    }

    public void setCadastres(List<CadastreMinimal> cadastres) {
        this.cadastres = cadastres;
    }

    public Long getLastCadastreListRefresh() {
        return lastCadastreListRefresh;
    }

    public void setLastCadastreListRefresh(Long lastCadastreListRefresh) {
        this.lastCadastreListRefresh = lastCadastreListRefresh;
    }
}
