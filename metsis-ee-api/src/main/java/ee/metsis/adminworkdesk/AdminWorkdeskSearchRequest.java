package ee.metsis.adminworkdesk;

import ee.finenet.fineframe.other.Range;
import ee.finenet.fineframe.utilities.BooleanUtility;
import spark.Request;

import java.util.List;
import java.util.Optional;

import static ee.finenet.fineframe.utilities.CollectionUtility.parseListFromCommaSepparatedString;
import static ee.finenet.fineframe.utilities.NumbersUtility.parseDoubleSilent;
import static ee.finenet.fineframe.utilities.NumbersUtility.parseLongSilent;
import static ee.finenet.fineframe.utilities.StringUtility.trimToNull;

public class AdminWorkdeskSearchRequest {
    private final List<String> counties;
    private final List<String> municipalities;
    private final Range<Double> area;
    private final Range<Double> totalForrestArea;
    private final Range<Double> forrestArea;
    private final Range<Double> arableArea;
    private final Conservations conservationAreas;
    private final List<String> suspended;
    private final boolean mustHavePhoneNumber;
    private final boolean mustNotHavePhoneNumber;
    private final boolean mustHaveNoStatus;
    private final boolean mustNotHaveForestPlan;
    private final List<String> assignees;
    private final String status;
    private final Long maxResults;
    private final List<String> ownerTypes;
    private final Long hasNotificationsSince;
    private final Long hasForrestPlanSince;
    private final Long statusUpdatedSince;
    private final Long statusUpdatedTo;

    AdminWorkdeskSearchRequest(Request req) {
        this.counties = parseListFromCommaSepparatedString(trimToNull(req.queryParams("counties")));
        this.municipalities = parseListFromCommaSepparatedString(trimToNull(req.queryParams("municipalities")));
        this.ownerTypes = parseListFromCommaSepparatedString(trimToNull(req.queryParams("ownerTypes")));
        this.area = parseRange("Area", req);
        this.totalForrestArea = parseRange("ForrestArea", req);
        this.forrestArea = parseRange("ForrestArea", req);
        this.arableArea = parseRange("ArableArea", req);
        this.conservationAreas = Conservations.fromString(req.queryParams("conservationAreas"));
        this.suspended = parseListFromCommaSepparatedString(req.queryParams("suspended"));
        this.mustHavePhoneNumber = BooleanUtility.parseBooleanSilent(req.queryParams("mustHavePhoneNumber"));
        this.mustNotHavePhoneNumber = BooleanUtility.parseBooleanSilent(req.queryParams("mustNotHavePhoneNumber"));
        this.mustHaveNoStatus = BooleanUtility.parseBooleanSilent(req.queryParams("mustHaveNoStatus"));
        this.mustNotHaveForestPlan = BooleanUtility.parseBooleanSilent(req.queryParams("mustNotHaveForestPlan"));
        this.assignees = parseListFromCommaSepparatedString(trimToNull(req.queryParams("assignees")));
        this.status = req.queryParams("status");
        this.maxResults = parseLongSilent(req.queryParams("maxResults"));
        this.hasNotificationsSince = parseLongSilent(req.queryParams("hasNotificationsSince"));
        this.hasForrestPlanSince = parseLongSilent(req.queryParams("hasForrestPlanSince"));
        this.statusUpdatedSince = parseLongSilent(req.queryParams("statusUpdatedSince"));
        this.statusUpdatedTo = parseLongSilent(req.queryParams("statusUpdatedTo"));
    }

    private Range<Double> parseRange(String key, Request req) {
        return new Range<>(parseDoubleSilent(req.queryParams("min" + key)), parseDoubleSilent(req.queryParams("max" + key)));
    }

    public List<String> getCounties() {
       return counties;
    }

    public List<String> getMunicipalities() {
        return municipalities;
    }

    public List<String> getOwnerTypes() {
        return ownerTypes;
    }

    public Range<Double> getArea() {
        return area;
    }

    public Range<Double> getTotalForrestArea() {
        return totalForrestArea;
    }

    public Range<Double> getForrestArea() {
        return forrestArea;
    }

    public Range<Double> getArableArea() {
        return arableArea;
    }

    public boolean mustHavePhoneNumber() {
        return mustHavePhoneNumber;
    }

    public boolean mustNotHavePhoneNumber() {
        return mustNotHavePhoneNumber;
    }

    public boolean mustHaveNoStatus() {
        return mustHaveNoStatus;
    }

    public boolean mustNotHaveForestPlan() {
        return mustNotHaveForestPlan;
    }

    public Optional<Long> getMaxResults() {
       return Optional.ofNullable(maxResults);
    }

    public Conservations getConservationAreas() {
        return conservationAreas;
    }

    public List<String> getSuspended() {
        return suspended;
    }

    public List<String> getAssignees() {
        return assignees;
    }

    public Optional<String> getStatus() {
        return Optional.ofNullable(status);
    }

    public Optional<Long> getHasNotificationsSince() {
        return Optional.ofNullable(hasNotificationsSince);
    }

    public Optional<Long> getHasForrestPlanSince() {
        return Optional.ofNullable(hasForrestPlanSince);
    }

    public Optional<Long> getStatusUpdatedSince() {
        return Optional.ofNullable(statusUpdatedSince);
    }

    public Optional<Long> getStatusUpdatedTo() {
        return Optional.ofNullable(statusUpdatedTo);
    }

    public enum Conservations {
        YES,
        NO,
        NOT_IMPORTANT;

        private static Conservations fromString(String given) {
            try {
                return Conservations.valueOf(given);
            } catch (Exception e) {
                return NO;
            }
        }
    }
}
