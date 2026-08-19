package ee.metsis.owners;

import ee.finenet.fineframe.utilities.CollectionUtility;
import spark.Request;

import java.util.Collections;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.stream.Collectors;

import static ee.finenet.fineframe.utilities.NumbersUtility.parseLongSilent;
import static ee.finenet.fineframe.utilities.StringUtility.trimToNull;


public class OwnerSearchCriteria {

    private final java.lang.String id;
    private final java.lang.String name;
    private final java.lang.String phone;
    private final java.lang.String email;
    private final java.lang.String orderBy;
    private final List<String> statuses;
    private final java.lang.String cadastre;
    private final java.lang.String direction;
    private java.lang.String assignee;
    private Long limit;

    public OwnerSearchCriteria(Request req) {
        this.id = trimToNull(req.queryParams("id"));
        this.name = trimToNull(req.queryParams("name"));
        this.phone = trimToNull(req.queryParams("phone"));
        this.email = trimToNull(req.queryParams("email"));
        this.limit = parseLongSilent(trimToNull(req.queryParams("limit")));
        this.orderBy = makeSureIsValidSortColumn(trimToNull(req.queryParams("orderBy")));
        this.direction = makeSureIsValidDirectionColumn(trimToNull(req.queryParams("direction")));
        this.statuses = CollectionUtility.commaSepparatedStringToList(trimToNull(req.queryParams("statuses")))
                .stream().filter(Objects::nonNull).collect(Collectors.toList());
        this.cadastre = req.queryParams("cadastre");
    }

    public OwnerSearchCriteria(String status, java.lang.String assignee, Long limit) {
        this.id = null;
        this.name = null;
        this.phone = null;
        this.email = null;
        this.orderBy = null;
        this.statuses = Collections.singletonList(status);
        this.direction = null;
        this.assignee = assignee;
        this.limit = limit;
        this.cadastre = null;
    }

    private java.lang.String makeSureIsValidSortColumn(java.lang.String orderBy) {
        if (orderBy == null) {
            return null;
        }
        return (orderBy.equals("id") || orderBy.equals("name") || orderBy.equals("status") || orderBy.equals("status_set_at")) ? orderBy : null;
    }

    private java.lang.String makeSureIsValidDirectionColumn(java.lang.String direction) {
        if (direction == null) {
            return null;
        }
        return (direction.equalsIgnoreCase("asc") || direction.equalsIgnoreCase("desc"))
                ? direction : null;
    }

    public Optional<java.lang.String> getId() {
        return Optional.ofNullable(id);
    }

    public Optional<java.lang.String> getName() {
        return Optional.ofNullable(name);
    }

    public Optional<java.lang.String> getPhone() {
        return Optional.ofNullable(phone);
    }

    public Optional<java.lang.String> getEmail() {
        return Optional.ofNullable(email);
    }

    public Optional<Long> getLimit() {
        return Optional.ofNullable(limit);
    }

    public Optional<java.lang.String> getAssignee() {
        return Optional.ofNullable(assignee);
    }

    public List<String> getStatuses() {
        return statuses;
    }

    public void setAssignee(java.lang.String assignee) {
        this.assignee = assignee;
    }

    public void setLimit(long limit) {
        this.limit = limit;
    }

    public Optional<java.lang.String> getOrderBy() {
        return Optional.ofNullable(orderBy);
    }

    public Optional<java.lang.String> getDirection() {
        return Optional.ofNullable(direction);
    }

    public Optional<java.lang.String> getCadastre() {
       return Optional.ofNullable(cadastre);
    }
}
