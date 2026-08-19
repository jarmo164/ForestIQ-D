package ee.metsis.workers;

import ee.finenet.fineframe.db.AbstractDAO;

import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.util.Date;

import javax.sql.DataSource;

public class LastOwnersUpdateDao extends AbstractDAO {

    public LastOwnersUpdateDao(DataSource ds) {
        super(ds);
    }

    public LocalDateTime getLastUpdate() {
        return queryForOne("select event_time from last_owners_cadastres_update", rs ->
                {
                    Date when = this.getTime("event_time", rs);
                    return LocalDateTime.ofInstant(Instant.ofEpochMilli(when.getTime()), ZoneId.systemDefault());
                }
        );
    }

    public void updateLastUpdate() {
        if (getLastUpdate() == null) {
            update("insert into last_owners_cadastres_update values (NOW())");
        } else {
            update("update last_owners_cadastres_update set event_time = NOW()");
        }
    }

}
