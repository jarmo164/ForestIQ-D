package ee.metsis.reminders;

import ee.metsis.owners.OwnerMinimal;

import java.util.Date;

public class Reminder {
    private Long id;
    private OwnerMinimal owner;
    private String text;
    private Date dueTime;
    private Date createdTime;
    private String creator;
    private String cadastre;
    private String propertyName;

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public OwnerMinimal getOwner() {
        return owner;
    }

    public void setOwner(OwnerMinimal owner) {
        this.owner = owner;
    }

    public String getText() {
        return text;
    }

    public void setText(String text) {
        this.text = text;
    }

    public Date getDueTime() {
        return dueTime;
    }

    public void setDueTime(Date dueTime) {
        this.dueTime = dueTime;
    }

    public void setCreator(String creator) {
        this.creator = creator;
    }

    public String getCreator() {
        return creator;
    }

    public String getOwnerId() {
        return owner == null ? null : owner.getId();
    }

    public Date getCreatedTime() {
        return createdTime;
    }

    public void setCreatedTime(Date createdTime) {
        this.createdTime = createdTime;
    }

    public String getCadastre() {
        return cadastre;
    }

    public void setCadastre(String cadastre) {
        this.cadastre = cadastre;
    }

    public String getPropertyName() {
        return propertyName;
    }

    public void setPropertyName(String propertyName) {
        this.propertyName = propertyName;
    }
}
