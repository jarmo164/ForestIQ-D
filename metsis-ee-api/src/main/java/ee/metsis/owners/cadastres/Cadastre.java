package ee.metsis.owners.cadastres;

import ee.finenet.fineframe.utilities.CollectionUtility;
import ee.metsis.owners.OwnerMinimal;
import ee.metsis.owners.cadastres.cadastrelabels.ForestPlanCadastreSubPart;
import ee.metsis.owners.cadastres.cadastrelabels.CadastreLabel;

import java.util.List;

public class Cadastre extends CadastreMinimal {
    private String municipality;
    private String county;
    private String address;
    private String regNr;
    private String postal;
    private List<ForestPlanCadastreSubPart> cadastreSubParts;
    private List<CadastreLabel> labels;
    private List<OwnerMinimal> owners;
    private Long mkDate;

    public String getMunicipality() {
        return municipality;
    }

    public void setMunicipality(String municipality) {
        this.municipality = municipality;
    }

    public String getCounty() {
        return county;
    }

    public void setCounty(String county) {
        this.county = county;
    }

    public String getAddress() {
        return address;
    }

    public void setAddress(String address) {
        this.address = address;
    }

    public String getRegNr() {
        return regNr;
    }

    public void setRegNr(String regNr) {
        this.regNr = regNr;
    }

    public String getPostal() {
        return postal;
    }

    public void setPostal(String postal) {
        this.postal = postal;
    }

    public List<OwnerMinimal> getOwners() {
        return owners;
    }

    public void setOwners(List<OwnerMinimal> owners) {
        this.owners = CollectionUtility.emptyIfNull(owners);
    }

    public List<CadastreLabel> getLabels() {
        return labels;
    }

    public void setLabels(List<CadastreLabel> labels) {
        this.labels = labels;
    }

    public List<ForestPlanCadastreSubPart> getCadastreSubParts() {
        return cadastreSubParts;
    }

    public void setCadastreSubParts(List<ForestPlanCadastreSubPart> cadastreSubParts) {
        this.cadastreSubParts = cadastreSubParts;
    }

    public Long getMkDate() {
        return mkDate;
    }

    public void setMkDate(Long mkDate) {
        this.mkDate = mkDate;
    }
}
