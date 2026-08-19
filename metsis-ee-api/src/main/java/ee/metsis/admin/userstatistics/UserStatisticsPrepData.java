package ee.metsis.admin.userstatistics;

import ee.finenet.fineframe.user.UserMinimal;

import java.util.List;

public class UserStatisticsPrepData {
    private final List<UserMinimal> users;
    private final List<String> ownerStatuses;

    public UserStatisticsPrepData(List<UserMinimal> users, List<String> ownerStatuses) {
        this.users = users;
        this.ownerStatuses = ownerStatuses;
    }

    public List<UserMinimal> getUsers() {
        return users;
    }

    public List<String> getOwnerStatuses() {
        return ownerStatuses;
    }
}
