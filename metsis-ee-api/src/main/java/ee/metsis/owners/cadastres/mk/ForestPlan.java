package ee.metsis.owners.cadastres.mk;

import ee.metsis.owners.cadastres.cadastrelabels.ForestPlanCadastreSubPart;

import java.util.List;

public class ForestPlan {
    private String cadastreNo;
    private List<ForestPlanCadastreSubPart> cadastreSubParts;
    private Long registrationDate;

    public String getCadastreNo() {
        return cadastreNo;
    }

    public void setCadastreNo(String cadastreNo) {
        this.cadastreNo = cadastreNo;
    }

    public List<ForestPlanCadastreSubPart> getCadastreSubParts() {
        return cadastreSubParts;
    }

    public void setCadastreSubParts(List<ForestPlanCadastreSubPart> cadastreSubParts) {
        this.cadastreSubParts = cadastreSubParts;
    }

    public Long getRegistrationDate() {
        return registrationDate;
    }

    public void setRegistrationDate(Long registrationDate) {
        this.registrationDate = registrationDate;
    }
}
