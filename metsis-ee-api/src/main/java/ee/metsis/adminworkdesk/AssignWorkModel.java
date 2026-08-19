package ee.metsis.adminworkdesk;

import java.util.List;

public class AssignWorkModel {
    private List<String> owners;
    private String assignee;
    private boolean reassign;

    public List<String> getOwners() {
        return owners;
    }

    public void setOwners(List<String> owners) {
        this.owners = owners;
    }

    public String getAssignee() {
        return assignee;
    }

    public void setAssignee(String assignee) {
        this.assignee = assignee;
    }

    public boolean isReassign() {
        return reassign;
    }

    public void setReassign(boolean reassign) {
        this.reassign = reassign;
    }
}
