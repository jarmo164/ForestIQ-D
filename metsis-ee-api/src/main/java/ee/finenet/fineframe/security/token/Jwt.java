package ee.finenet.fineframe.security.token;

import com.auth0.jwt.JWT;
import com.auth0.jwt.JWTCreator;
import com.auth0.jwt.algorithms.Algorithm;
import com.auth0.jwt.exceptions.JWTVerificationException;
import com.auth0.jwt.interfaces.Claim;
import com.auth0.jwt.interfaces.DecodedJWT;
import ee.finenet.fineframe.exceptions.FineFrameException;
import ee.finenet.fineframe.exceptions.UnauthorizedException;

import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.UUID;

public class Jwt {

    private static final String CLAIM_USER_ID = "userId";
    private static final String CLAIM_USER_NAME = "userName";
    private static final String CLAIM_PRIVILEGES = "privileges";
    private static final String CLAIM_TOTP_SHARED_SECRET = "totpsecret";

    private final Algorithm algorithm;

    public Jwt(Algorithm algorithm) {
        this.algorithm = algorithm;
    }

    public String encode(AuthToken authToken) {
        JWTCreator.Builder jwtBuilder = JWT.create()
                .withJWTId(authToken.getId())
                .withIssuedAt(authToken.getCreatedAt())
                .withExpiresAt(authToken.getExpiresAt())
                .withClaim(CLAIM_USER_ID, authToken.getUserId())
                .withClaim(CLAIM_USER_NAME, authToken.getUsersFullName())
                .withArrayClaim(CLAIM_PRIVILEGES, authToken.getPrivileges().toArray(new String[0]));
        if (authToken.getTotpSharedSecret() != null) {
            jwtBuilder.withClaim(CLAIM_TOTP_SHARED_SECRET, authToken.getTotpSharedSecret());
        }
        return jwtBuilder.sign(algorithm);
    }

    public AuthToken decodeAndValidate(String encodedToken) {
        try {
            DecodedJWT jwt = JWT.require(algorithm).build().verify(encodedToken);

            String tokenId = required(jwt.getId(), "id");
            Date issuedAt = required(jwt.getIssuedAt(), "issuedAt");
            Date expiresAt = required(jwt.getExpiresAt(), "expiresAt");
            String userId = required(jwt.getClaim(CLAIM_USER_ID), CLAIM_USER_ID).asString();
            String userName = required(jwt.getClaim(CLAIM_USER_NAME), CLAIM_USER_NAME).asString();
            List<String> privileges =
                    new ArrayList<>(required(jwt.getClaim(CLAIM_PRIVILEGES), "privileges")
                            .asList(String.class));
            AuthToken authToken = new AuthToken(UUID.fromString(tokenId), userId, userName, privileges, issuedAt, expiresAt);
            authToken.setTotpSharedSecret(jwt.getClaim(CLAIM_TOTP_SHARED_SECRET).asString());
            return authToken;
        } catch (Exception e) {
            if (e instanceof FineFrameException) {
                throw e;
            }
            throw new UnauthorizedException(e);
        }
    }

    private <T> T required(T object, String name) {
        if (object == null) {
            throw new JWTVerificationException(String.format("Mandatory claim '%s' is missing from the token", name));
        }
        if (object instanceof Claim) {
            Claim claim = (Claim) object;
            if (claim.isNull()) {
                throw new JWTVerificationException(String.format("Mandatory claim '%s' is missing from the token", name));
            }
        }
        return object;
    }
}
