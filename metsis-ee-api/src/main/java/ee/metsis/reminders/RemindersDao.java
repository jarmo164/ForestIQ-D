package ee.metsis.reminders;

import ee.finenet.fineframe.db.AbstractDAO;
import ee.finenet.fineframe.db.DBUtility;
import ee.metsis.owners.OwnerMinimal;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

import javax.sql.DataSource;

public class RemindersDao extends AbstractDAO {
    public RemindersDao(DataSource ds) {
        super(ds);
    }

    public List<Reminder> getMyReminders(String myUserName) {
        return queryForList(
                "select " +
                        "r.id as rid, " +
                        "r.duetime as rduetime, " +
                        "r.created_time as rcreated_time, " +
                        "r.reminder_text as rtext, " +
                        "r.creator as rcreator, " +
                        "r.cadastre as rcadastre, " +
                        "r.property_name as rproperty_name, " +
                        "o.id as oid, " +
                        "o.name as oname " +
                        "from reminders r " +
                        "left join owners o on " +
                        "o.id = r.owner_id " +
                        "where creator = ? order by r.duetime asc",
                rs -> {
                    Reminder reminder = new Reminder();
                    reminder.setId(getLong("rid", rs));
                    reminder.setDueTime(getTime("rduetime", rs));
                    reminder.setCreatedTime(getTime("rcreated_time", rs));
                    reminder.setCreator(getString("rcreator", rs));
                    reminder.setCadastre(getString("rcadastre", rs));
                    reminder.setPropertyName(getString("rproperty_name", rs));
                    OwnerMinimal ownerMinimal = new OwnerMinimal();
                    ownerMinimal.setId(getString("oid", rs));
                    ownerMinimal.setName(getString("oname", rs));
                    reminder.setOwner(ownerMinimal);
                    reminder.setText(getString("rtext", rs));
                    return reminder;
                }, myUserName);
    }

    public List<Reminder> getFutureReminders(List<String> usernames) {
        StringBuilder sql = new StringBuilder("select " +
                "r.id as rid, " +
                "r.duetime as rduetime, " +
                "r.created_time as rcreated_time, " +
                "r.reminder_text as rtext, " +
                "r.creator as rcreator, " +
                "r.cadastre as rcadastre, " +
                "r.property_name as rproperty_name, " +
                "o.id as oid, " +
                "o.name as oname " +
                "from reminders r " +
                "left join owners o on " +
                "o.id = r.owner_id " +
                "where r.duetime >= now() ");
        List<Object> params = new ArrayList<>();
        if (!usernames.isEmpty()) {
            sql.append(" and creator in (").append(DBUtility.createQMarks(usernames.size())).append(") ");
            params.addAll(usernames);
        }
        return queryForList(
                sql.toString() + " order by r.duetime asc",
                rs -> {
                    Reminder reminder = new Reminder();
                    reminder.setId(getLong("rid", rs));
                    reminder.setDueTime(getTime("rduetime", rs));
                    reminder.setCreatedTime(getTime("rcreated_time", rs));
                    reminder.setCreator(getString("rcreator", rs));
                    reminder.setCadastre(getString("rcadastre", rs));
                    reminder.setPropertyName(getString("rproperty_name", rs));
                    OwnerMinimal ownerMinimal = new OwnerMinimal();
                    ownerMinimal.setId(getString("oid", rs));
                    ownerMinimal.setName(getString("oname", rs));
                    reminder.setOwner(ownerMinimal);
                    reminder.setText(getString("rtext", rs));
                    return reminder;
                }, params.toArray());
    }

    public void addReminder(Reminder reminder, String creator) {
        update("insert into reminders (duetime, reminder_text, owner_id, creator, cadastre, property_name, " +
                        "created_time) values (?, ?, ?, ?, ?, ?, NOW())",
                DBUtility.fromUtiltoSqlTimestamp(reminder.getDueTime()),
                reminder.getText(),
                reminder.getOwnerId(),
                creator,
                reminder.getCadastre(),
                reminder.getPropertyName()
        );
    }

    public void deleteReminder(Long id) {
        update("delete from reminders where id = ?", id);
    }

    public List<Reminder> getOverdueRemindersForUser(String username) {
        return getMyReminders(username).stream().filter(reminder -> reminder.getDueTime().toInstant().isBefore(Instant.now())).collect(Collectors.toList());
    }
}
