package ee.finenet.fineframe.security.totp;

public class TotpLoginResponseModel {
    private final String token;

    public TotpLoginResponseModel(String token) {
        this.token = token;
    }

    public String getToken() {
        return token;
    }
}
