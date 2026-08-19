package ee.finenet.fineframe.user;

import java.util.Collections;
import java.util.List;
import java.util.Objects;

public class MaintainableUser extends UserMinimal {
    private List<String> privileges;

    public MaintainableUser() {
    }

    public MaintainableUser(String id, String name) {
        this(id, name, Collections.emptyList());
    }


    public MaintainableUser(String id, String name, List<String> privileges) {
        super(id, name);
        this.privileges = privileges;
    }

    public List<String> getPrivileges() {
        return privileges;
    }

    public void setPrivileges(List<String> privileges) {
        this.privileges = privileges;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        ee.finenet.fineframe.user.MaintainableUser that = (ee.finenet.fineframe.user.MaintainableUser) o;
        return Objects.equals(getId(), that.getId()) &&
                Objects.equals(getName(), that.getName()) &&
                Objects.equals(privileges, that.privileges);
    }

    @Override
    public int hashCode() {
        return Objects.hash(getId(), getName(), privileges);
    }
}
