package ee.metsis.admin.userstatistics;

import java.util.List;

public class UserOwnerStatusChangeStatistics {

    private final String userId;
    private final List<UserOwnerStatusChangeStatisticsFrame> statisticsFrame;

    public UserOwnerStatusChangeStatistics(String userId, List<UserOwnerStatusChangeStatisticsFrame> statisticsFrame) {
        this.userId = userId;
        this.statisticsFrame = statisticsFrame;
    }

    public String getUserId() {
        return userId;
    }

    public List<UserOwnerStatusChangeStatisticsFrame> getStatisticsFrame() {
        return statisticsFrame;
    }
}
