package ee.finenet.fineframe.user;

import ee.finenet.fineframe.utilities.StringUtility;

public class UserMinimal {
    private String id;
    private String name;

    public UserMinimal() {
    }

    public UserMinimal(String id, String name) {
        this.id = id;
        this.name = name;
    }

    public UserMinimal(ee.finenet.fineframe.user.UserMinimal user) {
        this(user.getId(), user.getName());
    }

    public String getId() {
        return StringUtility.emptyIfNull(id).trim();
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getName() {
        return StringUtility.emptyIfNull(name).trim();
    }

    public void setName(String name) {
        this.name = name;
    }
}
