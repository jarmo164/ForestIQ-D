package ee.metsis.owners;

import ee.finenet.fineframe.user.UserMinimal;

import java.util.Date;

public class OwnerMinimal {
    private String id;
    private String name;
    private String status;
    private Date statusSetAt;
    private UserMinimal assignee;
    private String phone;

    public OwnerMinimal() {
    }

    public OwnerMinimal(String id, String name, String status, Date statusSetAt, UserMinimal assignee, String phone) {
        this.id = id;
        this.name = name;
        this.status = status;
        this.statusSetAt = statusSetAt;
        this.assignee = assignee;
        this.phone = phone;
    }

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public Date getStatusSetAt() {
        return statusSetAt;
    }

    public void setStatusSetAt(Date statusSetAt) {
        this.statusSetAt = statusSetAt;
    }


    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public UserMinimal getAssignee() {
        return assignee;
    }

    public void setAssignee(UserMinimal assignee) {
        this.assignee = assignee;
    }

    public String getPhone() {
        return phone;
    }

    public void setPhone(String phone) {
        this.phone = phone;
    }
}
