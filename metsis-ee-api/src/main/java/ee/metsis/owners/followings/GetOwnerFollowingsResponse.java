package ee.metsis.owners.followings;

import java.util.List;

public class GetOwnerFollowingsResponse {
    private final List<String> followers;
    private final List<String> potentialFollowers;

    public GetOwnerFollowingsResponse(List<String> followers, List<String> potentialFollowers) {
        this.followers = followers;
        this.potentialFollowers = potentialFollowers;
    }

    public List<String> getFollowers() {
        return followers;
    }

    public List<String> getPotentialFollowers() {
        return potentialFollowers;
    }
}
