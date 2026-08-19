package ee.metsis.owners.logservice;

import ee.finenet.fineframe.utilities.StringUtility;

public class LogMessage {

    private Long id;
    private String owner;
    private String creator;
    private Long timestamp;
    private String message;
    private String ownersAssignee;

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getOwner() {
        return owner;
    }

    public void setOwner(String owner) {
        this.owner = owner;
    }

    public void setOwnersAssignee(String ownersAssignee) {
        this.ownersAssignee = ownersAssignee;
    }

    public String getOwnersAssignee() {
        return ownersAssignee;
    }

    public boolean ownersAssigneeIsSetAndIsNotLogMessageCreator() {
        return !StringUtility.isNullOrBlank(ownersAssignee) && !ownersAssignee.equals(creator);
    }

    public String getCreator() {
        return creator;
    }

    public void setCreator(String creator) {
        this.creator = creator;
    }

    public Long getTimestamp() {
        return timestamp;
    }

    public void setTimestamp(Long timestamp) {
        this.timestamp = timestamp;
    }

    public String getMessage() {
        return message == null ? null : message.substring(0, Math.min(message.length(), 10000));
    }

    public void setMessage(String message) {
        this.message = message;
    }
}
