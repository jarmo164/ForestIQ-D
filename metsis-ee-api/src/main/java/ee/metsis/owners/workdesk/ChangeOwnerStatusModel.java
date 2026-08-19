package ee.metsis.owners.workdesk;

import ee.finenet.fineframe.exceptions.BadRequestException;

import static java.util.Objects.requireNonNull;

public class ChangeOwnerStatusModel {

    private java.lang.String newStatus;
    private java.lang.String comment;

    public String getNewStatus() {
        try {
            return requireNonNull(String.valueOf(requireNonNull(newStatus)));
        } catch (Exception e) {
            throw new BadRequestException("UNKNOWN_OWNER_STATUS");
        }
    }

    public void setNewStatus(java.lang.String newStatus) {
        this.newStatus = newStatus;
    }

    public java.lang.String getComment() {
        return comment;
    }

    public void setComment(java.lang.String comment) {
        this.comment = comment;
    }
}
