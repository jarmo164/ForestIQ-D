package ee.metsis.messages;

import java.util.List;

public class NewDirectMessage {
    private String message;
    private List<String> recipients;

    public String getMessage() {
        return message;
    }

    public void setMessage(String message) {
        this.message = message;
    }

    public List<String> getRecipients() {
        return recipients;
    }

    public void setRecipients(List<String> recipients) {
        this.recipients = recipients;
    }
}
