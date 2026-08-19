package ee.metsis.owners.workdesk.ownerstatus;

import java.util.Date;

public class OwnerDisabledInAdminSearchToken {

    private final String reason;
    private final Date validFrom;
    private final Date validUntil;

    public OwnerDisabledInAdminSearchToken(String reason, Date validFrom, Date validUntil) {
        this.reason = reason;
        this.validFrom = validFrom;
        this.validUntil = validUntil;
    }

    public String getReason() {
        return reason;
    }

    public Date getValidFrom() {
        return validFrom;
    }

    public Date getValidUntil() {
        return validUntil;
    }
}
