package ee.metsis.owners.workdesk.ownerstatus;

import java.time.Duration;
import java.time.Instant;
import java.util.Date;

public class OwnerStatus {
    private String id;
    private String colorHex;
    private int durationDays;
    private boolean protectedReason;

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getColorHex() {
        return colorHex;
    }

    public void setColorHex(String colorHex) {
        this.colorHex = colorHex;
    }

    public int getDurationDays() {
        return durationDays;
    }

    public void setDurationDays(int durationDays) {
        this.durationDays = durationDays;
    }

    public boolean isProtectedReason() {
        return protectedReason;
    }

    public void setProtectedReason(boolean protectedReason) {
        this.protectedReason = protectedReason;
    }

    public OwnerDisabledInAdminSearchToken releaseOwnerOutOfSearchToken() {
        Instant from = Instant.now();
        Instant until = from.plus(Duration.ofDays(getDurationDays()));;
        return new OwnerDisabledInAdminSearchToken(
                id,
                new Date(from.toEpochMilli()),
                new Date(until.toEpochMilli())
        );
    }
}
