package ee.metsis.adminworkdesk;

import ee.finenet.fineframe.user.UserMinimal;

import java.util.List;

public class AdminWorkdeskPreparationData {
    private final List<String> counties;
    private final List<String> municipalities;
    private final List<UserMinimal> callers;
    private final List<String> statuses;
    private final List<String> ownerTypes;

    public AdminWorkdeskPreparationData(List<String> counties, List<String> municipalities, List<UserMinimal> callers, List<String> ownerTypes, List<String> statuses) {
        this.counties = counties;
        this.municipalities = municipalities;
        this.callers = callers;
        this.statuses = statuses;
        this.ownerTypes = ownerTypes;
    }

    public List<String> getCounties() {
        return counties;
    }

    public List<String> getMunicipalities() {
        return municipalities;
    }

    public List<UserMinimal> getCallers() {
        return callers;
    }

    public List<String> getStatuses() {
        return statuses;
    }

    public List<String> getOwnerTypes() {
        return ownerTypes;
    }

}
