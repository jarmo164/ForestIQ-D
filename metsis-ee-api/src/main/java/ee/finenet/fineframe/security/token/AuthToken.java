package ee.finenet.fineframe.security.token;

import ee.finenet.fineframe.utilities.CollectionUtility;

import java.util.Collections;
import java.util.Date;
import java.util.List;
import java.util.Objects;
import java.util.UUID;

import static java.util.Objects.requireNonNull;

public class AuthToken {

    private final String id;
    private final String userId;
    private final String usersFullName;
    private final List<String> privileges;
    private final Date createdAt;
    private final Date expiresAt;
    private String totpSharedSecret; // Only filled while registering TOTP

    public AuthToken(UUID id, String userId, String usersFullName, List<String> privileges, Date createdAt, Date expiresAt) {
        requireNonNull(id, "AuthToken.id must not be null");
        requireNonNull(userId, "AuthToken.userId must not be null");
        requireNonNull(usersFullName, "AuthToken.usersFullName must not be null");
        requireNonNull(privileges, "AuthToken.privileges must not be null");
        requireNonNull(createdAt, "AuthToken.createdAt must not be null");
        requireNonNull(expiresAt, "AuthToken.expiresAt must not be null");
        this.id = id.toString();
        this.userId = userId;
        this.usersFullName = usersFullName;
        this.privileges = CollectionUtility.emptyIfNull(privileges);
        this.createdAt = createdAt;
        this.expiresAt = expiresAt;
    }

    public String getId() {
        return id;
    }

    public String getUserId() {
        return userId;
    }

    public String getUsersFullName() {
        return usersFullName;
    }

    public List<String> getPrivileges() {
        return privileges == null ? Collections.emptyList() : privileges;
    }

    public Date getCreatedAt() {
        return createdAt;
    }

    public Date getExpiresAt() {
        return expiresAt;
    }

    public String getTotpSharedSecret() {
        return totpSharedSecret;
    }

    public void setTotpSharedSecret(String totpSharedSecret) {
        this.totpSharedSecret = totpSharedSecret;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        ee.finenet.fineframe.security.token.AuthToken authToken = (ee.finenet.fineframe.security.token.AuthToken) o;
        return Objects.equals(id, authToken.id) &&
                Objects.equals(userId, authToken.userId) &&
                Objects.equals(usersFullName, authToken.usersFullName) &&
                Objects.equals(privileges, authToken.privileges) &&
                Objects.equals(createdAt, authToken.createdAt) &&
                Objects.equals(expiresAt, authToken.expiresAt);
    }

    @Override
    public int hashCode() {
        return Objects.hash(id, userId, usersFullName, privileges, createdAt, expiresAt);
    }
}
