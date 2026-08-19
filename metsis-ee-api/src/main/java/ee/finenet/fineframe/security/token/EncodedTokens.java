package ee.finenet.fineframe.security.token;

import java.util.Objects;

public class EncodedTokens {
    private final EncodedToken actualToken;
    private final EncodedToken refreshToken;

    public EncodedTokens(EncodedToken actualToken, EncodedToken refreshToken) {
        Objects.requireNonNull(actualToken, "EncodedTokens.actualToken may not be null");
        Objects.requireNonNull(refreshToken, "EncodedTokens.refreshToken may not be null");
        this.actualToken = actualToken;
        this.refreshToken = refreshToken;
    }

    public EncodedToken getActualToken() {
        return actualToken;
    }

    public EncodedToken getRefreshToken() {
        return refreshToken;
    }
}
