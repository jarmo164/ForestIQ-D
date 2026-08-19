package ee.metsis.security;


import com.google.gson.reflect.TypeToken;

import java.lang.reflect.Type;
import java.util.List;

public enum Privilege {
    TOTP,
    TOKEN_REFRESH,
    ADMIN,
    OWNER_PROFILE,
    ASSIGNED_OWNERS,
    PHONES,
    EVALUATION;

    public static final Type GSON_LIST_TYPE = new TypeToken<List<Privilege>>() {
    }.getType();

    @Override
    public String toString() {
        return this.name();
    }
}
