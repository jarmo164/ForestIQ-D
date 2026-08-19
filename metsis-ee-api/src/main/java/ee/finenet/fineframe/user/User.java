package ee.finenet.fineframe.user;

import java.util.Collections;
import java.util.List;

import static java.util.Objects.requireNonNull;

public class User {
    private final String id;
    private final String name;
    private final List<String> privileges;
    private final String passwordHash;
    private final String totpSecret;
    private final boolean ivisible;

    public User(String id, String name, List<String> privileges, String passwordHash, String totpSecret, boolean ivisible) {
        requireNonNull(id, "User.id must not be null");
        requireNonNull(id, "User.name must not be null");
        requireNonNull(privileges, "User.privileges must not be null");
        requireNonNull(passwordHash, "User.passwordHash must not be null");
        this.id = id;
        this.name = name;
        this.privileges = privileges;
        Collections.sort(this.privileges);
        this.passwordHash = passwordHash;
        this.totpSecret = totpSecret;
        this.ivisible = ivisible;
    }

    public String getId() {
        return id;
    }

    public String getPasswordHash() {
        return passwordHash;
    }

    public String getName() {
        return name;
    }

    public List<String> getPrivileges() {
        return privileges;
    }

    public String getTotpSecret() {
        return totpSecret;
    }

    public boolean isIvisible() {
        return ivisible;
    }

    @Override
    public String toString() {
        return "User{" +
                "id='" + id + '\'' +
                '}';
    }

    public boolean isTotpEnabled() {
        return totpSecret != null;
    }
}
