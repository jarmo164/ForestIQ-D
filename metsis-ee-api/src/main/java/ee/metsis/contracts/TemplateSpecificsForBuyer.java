package ee.metsis.contracts;

public class TemplateSpecificsForBuyer {
    private String footerText;
    private byte[] headerLogo;

    public String getFooterText() {
        return footerText;
    }

    public void setFooterText(String footerText) {
        this.footerText = footerText;
    }

    public byte[] getHeaderLogo() {
        return headerLogo;
    }

    public void setHeaderLogo(byte[] headerLogo) {
        this.headerLogo = headerLogo;
    }
}
