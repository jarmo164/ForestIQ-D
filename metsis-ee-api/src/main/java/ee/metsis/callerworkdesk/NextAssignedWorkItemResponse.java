package ee.metsis.callerworkdesk;

public class NextAssignedWorkItemResponse {
    private final String ownerId;

    public NextAssignedWorkItemResponse(String ownerId) {
        this.ownerId = ownerId;
    }

    public String getOwnerId() {
        return ownerId;
    }
}
