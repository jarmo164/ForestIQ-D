package ee.metsis.messages;

import ee.finenet.fineframe.db.AbstractDAO;

import java.util.Date;
import java.util.List;

import javax.sql.DataSource;

public class MessagesDao extends AbstractDAO {
    public MessagesDao(DataSource ds) {
        super(ds);
    }

    public void createMessage(Message message) {
        long time = new Date().getTime();
        java.sql.Timestamp date = new java.sql.Timestamp(time);
        update("insert into messages (message, created_at, sender, recipient) values(?, ?, ?, ?)",
                message.getMessage(),
                date,
                message.getSender(),
                message.getRecipient());
    }

    public void markMessagesUpToSpecifiedDateNoticed(Date date, String receiver) {
        java.sql.Timestamp d = new java.sql.Timestamp(date.getTime());
        update("update messages set noticed_at = ? where recipient = ? and created_at <= ?",
                d,
                receiver,
                d);
    }

    public Long getNumberOfUnnoticedMessages(String receiver) {
        return queryForOne("select count(*) as cnt from messages where recipient = ? and noticed_at is null",
                rs -> getLong(
                        "cnt", rs), receiver);
    }

    public List<Message> getNewestReceivedMessagesWithSizeAndOffset(String receiver, int size, int offset) {
        return queryForList("select id, message, created_at, noticed_at, sender, recipient from messages where " +
                        "recipient" +
                        " = ? order by created_at desc limit ? offset ?",
                rs -> {
                    Message message = new Message();
                    message.setId(getLong("id" , rs));
                    message.setCreatedAt(getTime("created_at" , rs));
                    message.setMessage(getString("message" , rs));
                    message.setSender(getString("sender" , rs));
                    message.setRecipient(getString("recipient" , rs));
                    message.setNoticedAt(getTime("noticed_at" , rs));
                    return message;
                }, receiver, size, offset);
    }

    public List<Message> getNewestSentMessagesWithSizeAndOffset(String sender, int size, int offset) {
        return queryForList("select id, message, created_at, noticed_at, sender, recipient from messages where " +
                        "sender" +
                        " = ? order by created_at desc limit ? offset ?",
                rs -> {
                    Message message = new Message();
                    message.setId(getLong("id" , rs));
                    message.setCreatedAt(getTime("created_at" , rs));
                    message.setMessage(getString("message" , rs));
                    message.setSender(getString("sender" , rs));
                    message.setRecipient(getString("recipient" , rs));
                    message.setNoticedAt(getTime("noticed_at" , rs));
                    return message;
                }, sender, size, offset);
    }

    public List<String> getUsernames() {
        return queryForList("select id from users where ivisible = false", rs -> getString("id", rs));
    }
}
