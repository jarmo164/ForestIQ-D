package ee.metsis.owners.logservice;

import ee.finenet.fineframe.db.AbstractDAO;

import java.util.List;

import javax.sql.DataSource;

public class OwnerLogDao extends AbstractDAO {

    public OwnerLogDao(DataSource ds) {
        super(ds);
    }

    public Long saveLogMessage(LogMessage logMessage) {
        return insert("insert into owner_log (creator, owner_id, message) values (?, ?, ?) returning id",
                rs -> getLong("id", rs),
                logMessage.getCreator(),
                logMessage.getOwner(),
                logMessage.getMessage());
    }

    public List<LogMessage> getOwnersWorkLog(String ownerId, Long allAfterId) {
        return queryForList("select * from owner_log where owner_id = ? and id >= ? order by timestamp desc", rs -> {
            LogMessage logMessage = new LogMessage();
            logMessage.setId(getLong("id", rs));
            logMessage.setTimestamp(getTime("timestamp", rs).getTime());
            logMessage.setCreator(getString("creator", rs));
            logMessage.setOwner(getString("owner_id", rs));
            logMessage.setMessage(getString("message", rs));
            return logMessage;
        }, ownerId, allAfterId);
    }
}
