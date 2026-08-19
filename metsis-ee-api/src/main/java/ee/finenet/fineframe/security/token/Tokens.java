package ee.finenet.fineframe.security.token;

import java.util.Objects;

public class Tokens {
    private final AuthToken actualToken;
    private final AuthToken refreshToken;

    public Tokens(AuthToken actualToken, AuthToken refreshToken) {
        Objects.requireNonNull(actualToken, "Tokens.actualToken may not be null");
        Objects.requireNonNull(refreshToken, "Tokens.refreshToken may not be null");
        this.actualToken = actualToken;
        this.refreshToken = refreshToken;
    }

    public AuthToken getActualToken() {
        return actualToken;
    }

    public AuthToken getRefreshToken() {
        return refreshToken;
    }
}
