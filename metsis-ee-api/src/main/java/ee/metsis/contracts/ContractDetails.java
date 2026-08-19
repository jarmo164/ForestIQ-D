package ee.metsis.contracts;

import java.util.Date;
import java.util.List;

public class ContractDetails {
    private Date dateOfEnforcement;
    private Date finalDate;
    private double price;
    private String writtenPrice;
    private Integer bankDaysToPayUp;
    private boolean bankDaysToPayUpCondition;
    private String additionalTerms;
    private List<ContractualCadastre> cadastres;
    private Double vat;
    private String vatWithWords;

    public Date getDateOfEnforcement() {
        return dateOfEnforcement;
    }

    public void setDateOfEnforcement(Date dateOfEnforcement) {
        this.dateOfEnforcement = dateOfEnforcement;
    }

    public Date getFinalDate() {
        return finalDate;
    }

    public void setFinalDate(Date finalDate) {
        this.finalDate = finalDate;
    }

    public double getPrice() {
        return price;
    }

    public void setPrice(double price) {
        this.price = price;
    }

    public String getWrittenPrice() {
        return writtenPrice;
    }

    public void setWrittenPrice(String writtenPrice) {
        this.writtenPrice = writtenPrice;
    }

    public Integer getBankDaysToPayUp() {
        return bankDaysToPayUp;
    }

    public void setBankDaysToPayUp(Integer bankDaysToPayUp) {
        this.bankDaysToPayUp = bankDaysToPayUp;
    }

    public List<ContractualCadastre> getCadastres() {
        return cadastres;
    }

    public void setCadastres(List<ContractualCadastre> cadastres) {
        this.cadastres = cadastres;
    }

    public String getAdditionalTerms() {
        return additionalTerms;
    }

    public void setAdditionalTerms(String additionalTerms) {
        this.additionalTerms = additionalTerms;
    }

    public Double getVat() {
        return vat;
    }

    public void setVat(Double vat) {
        this.vat = vat;
    }

    public String getVatWithWords() {
        return vatWithWords;
    }

    public void setVatWithWords(String vatWithWords) {
        this.vatWithWords = vatWithWords;
    }

    public boolean isBankDaysToPayUpCondition() {
        return bankDaysToPayUpCondition;
    }

    public void setBankDaysToPayUpCondition(boolean bankDaysToPayUpCondition) {
        this.bankDaysToPayUpCondition = bankDaysToPayUpCondition;
    }
}
