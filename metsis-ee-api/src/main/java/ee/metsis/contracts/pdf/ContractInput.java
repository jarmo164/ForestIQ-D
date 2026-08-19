package ee.metsis.contracts.pdf;

import ee.metsis.contracts.BuyerParty;
import ee.metsis.contracts.ContractData;
import ee.metsis.contracts.ContractDetails;
import ee.metsis.contracts.ContractualCadastre;
import ee.metsis.contracts.ForestSection;
import ee.metsis.contracts.SellerParty;

import java.text.DateFormat;
import java.text.DecimalFormat;
import java.text.SimpleDateFormat;
import java.util.List;

import static org.apache.commons.lang.StringUtils.trimToNull;

public class ContractInput {

    private static final DateFormat DATE_FORMAT = new SimpleDateFormat("dd.MM.yyyy");
    private static final DecimalFormat DECIMAT_FORMAT_2_AFTER_COMMA = new DecimalFormat("0.00");
    private static final DecimalFormat DECIMAT_FORMAT_1_AFTER_COMMA = new DecimalFormat("0.0");

    private final String contractNumber;
    private final String dateOfEnforcement;
    private final String finalDate;
    private final String priceNumeric;
    private final String priceWritten;
    private final String vat;
    private final String vatWritten;
    private final boolean vattable;
    private final String bankDaysToPayUpNumeric;
    private final String bankDaysToPayUpWritten;
    private final Boolean bankDaysToPayUpCondition;
    private final String additionalTerms;
    private final String totalCutArea;
    private final String totalCutTm;
    private final BuyerParty buyer;
    private final List<SellerParty> sellers;
    private final List<ContractualCadastre> cadastres;

    public ContractInput(ContractData data) {
        ContractDataValidator.validate(data);
        this.contractNumber = data.getContractNumber();
        ContractDetails details = data.getContractDetails();
        this.dateOfEnforcement = DATE_FORMAT.format(details.getDateOfEnforcement());
        this.finalDate = DATE_FORMAT.format(details.getFinalDate());
        this.priceNumeric = formatMoney(details.getPrice());
        this.priceWritten = details.getWrittenPrice();
        Double vat = details.getVat();
        this.vattable = vat != null && vat != 0.0;
        this.vat = formatMoney(vat);
        this.vatWritten = details.getVatWithWords();
        this.bankDaysToPayUpNumeric = details.getBankDaysToPayUp().toString();
        this.bankDaysToPayUpWritten = numberToEstonian(details.getBankDaysToPayUp());
        this.bankDaysToPayUpCondition = details.isBankDaysToPayUpCondition();
        this.additionalTerms = trimToNull(details.getAdditionalTerms());
        this.buyer = data.getBuyer();
        this.sellers = data.getSellers();
        List<ContractualCadastre> cadastres = details.getCadastres();
        this.cadastres = cadastres;
        this.totalCutArea = formatDouble(cadastres.stream().map(ContractualCadastre::getForestSections)
                .mapToDouble(sectionsOfCadastre -> sectionsOfCadastre.stream().mapToDouble(ForestSection::getArea).sum())
                .sum());
        this.totalCutTm = formatDouble(cadastres.stream().map(ContractualCadastre::getForestSections)
                .mapToDouble(sectionsOfCadastre -> sectionsOfCadastre.stream().mapToDouble(ForestSection::getAmountToBeCut).sum())
                .sum());
    }

    private String numberToEstonian(Integer bankDaysToPayUp) {
        if (bankDaysToPayUp < 1 || bankDaysToPayUp > 30) {
            return "";
        }
        switch (bankDaysToPayUp) {
            case 1:
                return "ühe";
            case 2:
                return "kahe";
            case 3:
                return "kolme";
            case 4:
                return "nelja";
            case 5:
                return "viie";
            case 6:
                return "kuue";
            case 7:
                return "seitsme";
            case 8:
                return "kaheksa";
            case 9:
                return "üheksa";
            case 10:
                return "kümne";
            case 11:
                return "üheteistkümne";
            case 12:
                return "kaheteistkümne";
            case 13:
                return "kolmeteistkümne";
            case 14:
                return "neljateistkümne";
            case 15:
                return "viieteistkümne";
            case 16:
                return "kuueteistkümne";
            case 18:
                return "seitsmeteistkümne";
            case 19:
                return "kaheksateistkümne";
            case 20:
                return "üheksateistkümne";
            case 21:
                return "kahekümne ühe";
            case 22:
                return "kahekümne kahe";
            case 23:
                return "kahekümne kolme";
            case 24:
                return "kahekümne nelja";
            case 25:
                return "kahekümne viie";
            case 26:
                return "kahekümne kuue";
            case 27:
                return "kahekümne seitsme";
            case 28:
                return "kahekümne kaheksa";
            case 29:
                return "kahekümne üheksa";
            case 30:
                return "kolmekümne";
        }
        return null;
    }

    private String formatMoney(Double d) {
        if (d == null) {
            return "0";
        }
        if (d.intValue() == d) {
            return "" + d.intValue();
        }
        return DECIMAT_FORMAT_2_AFTER_COMMA.format(d);
    }

    private String formatDouble(Double d) {
        if (d.intValue() == d) {
            return "" + d.intValue();
        }
        return DECIMAT_FORMAT_1_AFTER_COMMA.format(d);
    }

    public String getContractNumber() {
        return contractNumber;
    }

    public String getDateOfEnforcement() {
        return dateOfEnforcement;
    }

    public String getFinalDate() {
        return finalDate;
    }

    public String getPriceNumeric() {
        return priceNumeric;
    }

    public String getPriceWritten() {
        return priceWritten;
    }

    public String getBankDaysToPayUpNumeric() {
        return bankDaysToPayUpNumeric;
    }

    public String getBankDaysToPayUpWritten() {
        return bankDaysToPayUpWritten;
    }

    public String getAdditionalTerms() {
        return additionalTerms;
    }

    public BuyerParty getBuyer() {
        return buyer;
    }

    public List<SellerParty> getSellers() {
        return sellers;
    }

    public List<ContractualCadastre> getCadastres() {
        return cadastres;
    }

    public String getTotalCutArea() {
        return totalCutArea;
    }

    public String getTotalCutTm() {
        return totalCutTm;
    }

    public String getVat() {
        return vat;
    }

    public String getVatWritten() {
        return vatWritten;
    }

    public boolean isVattable() {
        return vattable;
    }

    public Boolean getBankDaysToPayUpCondition() {
        return bankDaysToPayUpCondition;
    }
}
