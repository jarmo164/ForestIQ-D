package ee.metsis.admin.userstatistics;

import java.util.Date;

public class UserOwnerStatusChangeStatisticsFrame {
    private final Date since;
    private final Long count;

    public UserOwnerStatusChangeStatisticsFrame(Date since, Long count) {
        this.since = since;
        this.count = count;
    }

    public Date getSince() {
        return since;
    }

    public Long getCount() {
        return count;
    }
}
