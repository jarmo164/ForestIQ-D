package ee.finenet.fineframe.security.totp;

public class TotpLoginRequestModel {
    private Long totpCode;

    public Long getTotpCode() {
        return totpCode;
    }

    public void setTotpCode(Long totpCode) {
        this.totpCode = totpCode;
    }
}
