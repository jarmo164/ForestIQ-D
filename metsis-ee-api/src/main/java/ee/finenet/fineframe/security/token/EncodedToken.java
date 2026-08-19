package ee.finenet.fineframe.security.token;

import java.util.Objects;

public class EncodedToken {
    private final String token;

    public EncodedToken(String token) {
        Objects.requireNonNull(token, "EncodedToken.token may not be null");
        this.token = token;
    }

    public String getToken() {
        return token;
    }
}
