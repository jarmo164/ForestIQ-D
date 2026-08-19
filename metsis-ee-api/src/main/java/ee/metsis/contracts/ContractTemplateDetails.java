package ee.metsis.contracts;

public class ContractTemplateDetails {
    private String footer;
    private byte[] logo;

    public String getFooter() {
        return footer;
    }

    public void setFooter(String footer) {
        this.footer = footer;
    }

    public byte[] getLogo() {
        return logo;
    }

    public void setLogo(byte[] logo) {
        this.logo = logo;
    }
}
