package ee.metsis.messages;

public class NewMessagesCount {
    private final long newMessageCount;

    public NewMessagesCount(long newMessageCount) {
        this.newMessageCount = newMessageCount;
    }

    public long getNewMessageCount() {
        return newMessageCount;
    }
}
