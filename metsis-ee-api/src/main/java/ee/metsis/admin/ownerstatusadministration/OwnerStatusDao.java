package ee.metsis.admin.ownerstatusadministration;

import ee.finenet.fineframe.db.AbstractDAO;
import ee.metsis.owners.workdesk.ownerstatus.OwnerStatus;

import java.util.List;

import javax.sql.DataSource;

public class OwnerStatusDao extends AbstractDAO {
    public OwnerStatusDao(DataSource ds) {
        super(ds);
    }

    public void deleteOwnerStatus(String id) {
        update("delete from owner_statuses where id = ?", id);
    }

    public void updateOwnerStatus(OwnerStatus ownerStatus) {
        update("update owner_statuses set days_out_of_search = ?, reason_color = ? where id = ?", ownerStatus.getDurationDays(), ownerStatus.getColorHex(), ownerStatus.getId());
    }

    public void createOwnerStatus(OwnerStatus ownerStatus) {
        update("insert into owner_statuses (id, protected, days_out_of_search, reason_color) values (?, false, ?, ?)", ownerStatus.getId(), ownerStatus.getDurationDays(), ownerStatus.getColorHex());
    }

    public List<OwnerStatus> getOwnerStatuses() {
        return queryForList("select * from owner_statuses order by protected, id", rs -> {
            ee.metsis.owners.workdesk.ownerstatus.OwnerStatus ownerStatus = new ee.metsis.owners.workdesk.ownerstatus.OwnerStatus();
            ownerStatus.setId(getString("id", rs));
            ownerStatus.setDurationDays(getInt("days_out_of_search", rs));
            ownerStatus.setProtectedReason(getBoolean("protected", rs));
            ownerStatus.setColorHex(getString("reason_color", rs));
            return ownerStatus;
        });
    }
}
