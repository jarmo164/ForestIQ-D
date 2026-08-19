package ee.metsis.contracts;

import java.text.DecimalFormat;
import java.text.DecimalFormatSymbols;
import java.text.NumberFormat;
import java.util.Locale;

public class SellerParty extends ContractParty {

    private static final DecimalFormat moneyFormatter = createMoneyFormatter();

    private static DecimalFormat createMoneyFormatter() {
        DecimalFormat moneyFormatter = (DecimalFormat) NumberFormat.getCurrencyInstance(Locale.forLanguageTag("et"));
        DecimalFormatSymbols symbols = moneyFormatter.getDecimalFormatSymbols();
        symbols.setCurrencySymbol("");
        moneyFormatter.setDecimalFormatSymbols(symbols);
        return moneyFormatter;
    }

    private String bankAccountNumber;
    private Double moneyObtainedFromTheDeal;
    private String vat;

    public String getVat() {
        return (vat == null || vat.trim().isEmpty()) ? null : vat.trim();
    }

    public void setVat(String vat) {
        this.vat = vat;
    }

    public String getBankAccountNumber() {
        return bankAccountNumber;
    }

    public void setBankAccountNumber(String bankAccountNumber) {
        this.bankAccountNumber = bankAccountNumber;
    }

    public String getMoneyObtainedFromTheDeal() {
        return formatMoney(moneyObtainedFromTheDeal);
    }

    public void setMoneyObtainedFromTheDeal(Double moneyObtainedFromTheDeal) {
        this.moneyObtainedFromTheDeal = moneyObtainedFromTheDeal;
    }

    public boolean isPrivatePerson() {
        try {
            int firstNumberOfCode = Integer.parseInt(this.getCode().substring(0, 1));
            return firstNumberOfCode >= 1 && firstNumberOfCode <= 6;
        } catch (Exception e) {
            return true;
        }
    }

    public static String formatMoney(Double d) {
        if (d == null) {
            return "0,00";
        }
        String formatted = moneyFormatter.format(d);
        return formatted.endsWith(",00") ? formatted.substring(0, formatted.length() - 3) : formatted;
    }
}
