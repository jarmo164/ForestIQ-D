package ee.metsis.users;

import ee.finenet.fineframe.db.AbstractDAO;
import ee.finenet.fineframe.db.DBUtility;

import java.util.ArrayList;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import javax.sql.DataSource;

public class UserOwnerStatusChangeStatisticsDAO extends AbstractDAO {

    public UserOwnerStatusChangeStatisticsDAO(DataSource ds) {
        super(ds);
    }

    public void createRecord(java.lang.String userId, String fromStatus, String toStatus) {
        update("insert into user_owner_status_change_statistics (user_id, from_status, to_status) values (?, ?, ?)",
                userId, fromStatus, toStatus);
    }

    public Map<java.lang.String, List<Date>> getStatisticalEventTimesByUser(List<java.lang.String> userIds, List<String> fromStatuses, List<String> toStatuses, Date since, Date upTo) {
        List<Object> params = new ArrayList<>();
        params.addAll(userIds);
        params.addAll(fromStatuses);
        params.addAll(toStatuses);
        params.add(DBUtility.fromUtiltoSqlTimestamp(since));
        params.add(DBUtility.fromUtiltoSqlTimestamp(upTo));
        Map<java.lang.String, List<Date>> result = new HashMap<>();
        queryForList("select s.* from user_owner_status_change_statistics s " +
                "where s.user_id in (" + DBUtility.createQMarks(userIds.size()) + ") " +
                "and s.from_status in (" + DBUtility.createQMarks(fromStatuses.size()) + ") " +
                "and s.to_status in (" + DBUtility.createQMarks(toStatuses.size()) + ") " +
                "and s.timestamp >= ? and s.timestamp <= ? order by s.timestamp asc", rs -> {
            java.lang.String userId = getString("user_id", rs);
            if (!result.containsKey(userId)) {
                result.put(userId, new ArrayList<>());
            }
            result.get(userId).add(getTime("timestamp", rs));
            return null;
        }, params.toArray());

        return result;
    }
}
