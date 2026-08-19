package ee.metsis.messages;

import java.util.Date;
import java.util.List;

public class MessagesService {
    private final MessagesDao messagesDao;

    public MessagesService(MessagesDao messagesDao) {
        this.messagesDao = messagesDao;
    }

    public void sendMessage(String messageText, String sender, String recipient) {
        Message message = new Message();
        message.setSender(sender);
        message.setRecipient(recipient);
        message.setMessage(messageText);
        messagesDao.createMessage(message);
    }

    public void markMessagesUpToSpecifiedDateNoticed(Date date, String recipient) {
        messagesDao.markMessagesUpToSpecifiedDateNoticed(date, recipient);
    }

    public Long getNumberOfUnnoticedMessages(String receiver) {
        return messagesDao.getNumberOfUnnoticedMessages(receiver);
    }

    public List<Message> getPageOfNewestReceivedMessages(String receiver, int pageSize, int pageNo) {
        return messagesDao.getNewestReceivedMessagesWithSizeAndOffset(receiver, pageSize, (pageNo - 1) * pageSize);
    }

    public List<Message> getPageOfNewestSentMessages(String sender, int pageSize, int pageNo) {
        return messagesDao.getNewestSentMessagesWithSizeAndOffset(sender, pageSize, (pageNo - 1) * pageSize);
    }

    public List<String> getUsernames() {
        return messagesDao.getUsernames();
    }
}
