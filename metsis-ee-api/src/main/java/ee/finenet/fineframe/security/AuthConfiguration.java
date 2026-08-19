package ee.finenet.fineframe.security;

import ee.finenet.fineframe.configuration.PropertyReadingInstruction;
import ee.finenet.fineframe.configuration.instructions.IntegerReadingInstruction;
import ee.finenet.fineframe.configuration.validators.MinSizeValidator;

import java.time.Duration;
import java.util.Objects;
import java.util.Properties;

public class AuthConfiguration {

    private final Duration usualTokenTTL;
    private final Duration totpTokenTTL;
    private final Duration refreshTokenTTL;

    public AuthConfiguration(Properties properties) {
        Objects.requireNonNull(properties, "AuthConfiguration.properties may not be null");
        this.usualTokenTTL = Duration.ofMinutes(new PropertyReadingInstruction<>(
                properties,
                "FINEFRAME_AUTH_USUAL_TOKEN_TTL_MIN",
                new MinSizeValidator(1),
                IntegerReadingInstruction.INSTANCE)
                .read());
        this.totpTokenTTL = Duration.ofMinutes(new PropertyReadingInstruction<>(
                properties,
                "FINEFRAME_AUTH_REFRESH_TOKEN_TTL_MIN",
                new MinSizeValidator(1),
                IntegerReadingInstruction.INSTANCE)
                .read());
        this.refreshTokenTTL = Duration.ofMinutes(new PropertyReadingInstruction<>(
                properties,
                "FINEFRAME_AUTH_TOTP_TOKEN_TTL_MIN",
                new MinSizeValidator(1),
                IntegerReadingInstruction.INSTANCE)
                .read());
    }

    public Duration getUsualTokenTTL() {
        return usualTokenTTL;
    }

    public Duration getTotpTokenTTL() {
        return totpTokenTTL;
    }

    public Duration getRefreshTokenTTL() {
        return refreshTokenTTL;
    }
}
