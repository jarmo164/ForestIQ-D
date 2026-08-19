package ee.metsis.owners.workdesk;

import ee.finenet.fineframe.user.UserMinimal;
import ee.metsis.owners.workdesk.ownerstatus.OwnerStatus;

import java.util.List;

public class OwnerStatusData {

    private List<UserMinimal> possibleAssignees;
    private UserMinimal assignee;
    private List<String> possibleOwnerStatuses;
    private OwnerStatus status;

    public List<UserMinimal> getPossibleAssignees() {
        return possibleAssignees;
    }

    public void setPossibleAssignees(List<UserMinimal> possibleAssignees) {
        this.possibleAssignees = possibleAssignees;
    }

    public UserMinimal getAssignee() {
        return assignee;
    }

    public void setAssignee(UserMinimal assignee) {
        this.assignee = assignee;
    }

    public List<String> getPossibleOwnerStatuses() {
        return possibleOwnerStatuses;
    }

    public void setPossibleOwnerStatuses(List<String> possibleOwnerStatuses) {
        this.possibleOwnerStatuses = possibleOwnerStatuses;
    }

    public OwnerStatus getStatus() {
        return status;
    }

    public void setStatus(OwnerStatus status) {
        this.status = status;
    }
}
