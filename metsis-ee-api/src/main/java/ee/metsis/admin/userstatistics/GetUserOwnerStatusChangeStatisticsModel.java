package ee.metsis.admin.userstatistics;

import ee.finenet.fineframe.utilities.CollectionUtility;
import ee.finenet.fineframe.utilities.StringUtility;
import spark.Request;

import java.time.Duration;
import java.util.ArrayList;
import java.util.Date;
import java.util.HashSet;
import java.util.List;
import java.util.stream.Collectors;

public class GetUserOwnerStatusChangeStatisticsModel {
    private final List<java.lang.String> userIds;
    private final List<String> fromStatuses;
    private final List<String> toStatuses;
    private final Duration granularity;
    private final Date since;
    private final Date upTo;

    public GetUserOwnerStatusChangeStatisticsModel(Request req) {
        this.userIds = uniqueList(CollectionUtility.commaSepparatedStringToList(req.queryParams("users")));
        this.fromStatuses = uniqueList(CollectionUtility.commaSepparatedStringToList(req.queryParams("fromStatuses")).stream().map(os -> StringUtility.isNullOrBlank(os) ? null : os).collect(Collectors.toList()));
        this.toStatuses = uniqueList(CollectionUtility.commaSepparatedStringToList(req.queryParams("toStatuses")).stream().map(os -> StringUtility.isNullOrBlank(os) ? null : os).collect(Collectors.toList()));
        this.granularity = parseGranularity(req.queryParams("granularity"));
        this.since = parseDate(req.queryParams("since"));
        Date upto = parseDate(req.queryParams("upTo"));
        this.upTo = upto == null ? new Date() : upto;
    }

    public List<java.lang.String> getUserIds() {
        return userIds;
    }

    public List<String> getFromStatuses() {
        return fromStatuses;
    }

    public List<String> getToStatuses() {
        return toStatuses;
    }

    public Duration getGranularity() {
        return granularity;
    }

    public Date getSince() {
        return since;
    }

    public Date getUpTo() {
        return upTo;
    }

    private <T> List<T> uniqueList(List<T> given) {
        return new ArrayList<>(new HashSet<>(CollectionUtility.emptyIfNull(given)));
    }

    private Duration parseGranularity(java.lang.String given) {
        if ("DAY".equalsIgnoreCase(given)) {
            return Duration.ofDays(1);
        }
        if ("HOUR".equalsIgnoreCase(given)) {
            return Duration.ofHours(1);
        }
        return null;
    }

    private Date parseDate(java.lang.String given) {
        try {
            return new Date(Long.parseLong(given));
        } catch (Exception e) {
            return null;
        }
    }
}
