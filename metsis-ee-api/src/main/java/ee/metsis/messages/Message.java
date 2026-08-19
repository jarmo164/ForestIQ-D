package ee.metsis.messages;

import java.util.Date;

public class Message {
    private Long id;
    private String message;
    private Date createdAt;
    private Date noticedAt;
    private String sender;
    private String recipient;

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getMessage() {
        return message;
    }

    public void setMessage(String message) {
        this.message = message;
    }

    public Date getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(Date createdAt) {
        this.createdAt = createdAt;
    }

    public Date getNoticedAt() {
        return noticedAt;
    }

    public void setNoticedAt(Date noticedAt) {
        this.noticedAt = noticedAt;
    }

    public String getSender() {
        return sender;
    }

    public void setSender(String sender) {
        this.sender = sender;
    }

    public String getRecipient() {
        return recipient;
    }

    public void setRecipient(String recipient) {
        this.recipient = recipient;
    }
}
