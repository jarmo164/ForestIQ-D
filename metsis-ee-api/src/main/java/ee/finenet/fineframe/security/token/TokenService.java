package ee.finenet.fineframe.security.token;

import ee.finenet.fineframe.security.AuthConfiguration;
import ee.finenet.fineframe.security.GenerealPrivileges;
import ee.finenet.fineframe.security.totp.TotpHandler;

import java.time.Duration;
import java.time.Instant;
import java.util.Collections;
import java.util.Date;
import java.util.List;
import java.util.Objects;

import static java.util.UUID.randomUUID;

public class TokenService {

    private final Duration usualTokenTTL;
    private final Duration refreshTokenTTL;
    private final Duration totpTokenTTL;

    public TokenService(AuthConfiguration configuration) {
        Objects.requireNonNull(configuration, "TokenService.configuration may not be null");
        this.usualTokenTTL = configuration.getUsualTokenTTL();
        this.refreshTokenTTL = configuration.getRefreshTokenTTL();
        this.totpTokenTTL = configuration.getTotpTokenTTL();
    }

    public AuthToken createFullToken(String userId, String usersName, List<String> privileges) {
        return createToken(userId, usersName, privileges, usualTokenTTL);
    }

    private AuthToken createToken(String userId, String usersName, List<String> privileges, Duration tokenTTL) {
        Instant now = Instant.now();
        Instant expiry = now.plus(tokenTTL);
        return new AuthToken(randomUUID(), userId, usersName, privileges, Date.from(now), Date.from(expiry));
    }

    public AuthToken createRefreshToken(String userId, String usersName) {
        Instant now = Instant.now();
        Instant expiry = now.plus(refreshTokenTTL);
        return new AuthToken(
                randomUUID(), userId, usersName, Collections.singletonList(GenerealPrivileges.TOKEN_REFRESH), Date.from(now), Date.from(expiry));
    }

    public AuthToken createTotpToken(String userId, String usersName) {
        return createToken(userId, usersName, Collections.singletonList(GenerealPrivileges.TOTP), totpTokenTTL);
    }

    public AuthToken createTotpRegistrationToken(String userId, String name) {
        AuthToken totpToken = createTotpToken(userId, name);
        totpToken.setTotpSharedSecret(TotpHandler.createSharedKey());
        return totpToken;
    }
}
