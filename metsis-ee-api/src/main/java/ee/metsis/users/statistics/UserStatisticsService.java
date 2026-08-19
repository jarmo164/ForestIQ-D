package ee.metsis.users.statistics;

import ee.finenet.fineframe.exceptions.BadRequestException;
import ee.finenet.fineframe.user.User;
import ee.finenet.fineframe.user.UserMinimal;
import ee.metsis.admin.ownerstatusadministration.OwnerStatusService;
import ee.metsis.admin.userstatistics.GetUserOwnerStatusChangeStatisticsModel;
import ee.metsis.admin.userstatistics.UserOwnerStatusChangeStatistics;
import ee.metsis.admin.userstatistics.UserOwnerStatusChangeStatisticsFrame;
import ee.metsis.admin.userstatistics.UserStatisticsPrepData;
import ee.metsis.users.UserDAO;
import ee.metsis.users.UserNotFoundException;
import ee.metsis.users.UserOwnerStatusChangeStatisticsDAO;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Date;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.stream.Collectors;

public class UserStatisticsService {

    private final UserDAO userDAO;
    private final UserOwnerStatusChangeStatisticsDAO userOwnerStatusChangeStatisticsDAO;
    private final OwnerStatusService ownerStatusService;

    public UserStatisticsService(UserDAO userDAO, UserOwnerStatusChangeStatisticsDAO userOwnerStatusChangeStatisticsDAO, OwnerStatusService ownerStatusService) {
        this.userDAO = userDAO;
        this.userOwnerStatusChangeStatisticsDAO = userOwnerStatusChangeStatisticsDAO;
        this.ownerStatusService = ownerStatusService;
    }

    public void createUserOwnerStatusChangeRecord(java.lang.String userId, String fromStatus, String toStatus) {
        Optional<User> user = userDAO.getUser(userId);
        if (user.isEmpty() || user.get().isIvisible()) {
            throw new UserNotFoundException();
        }
        userOwnerStatusChangeStatisticsDAO.createRecord(userId, fromStatus, toStatus);
    }

    public List<UserOwnerStatusChangeStatistics> getUsersOwnerStatusChangeStatistics(GetUserOwnerStatusChangeStatisticsModel criteria) {

        List<java.lang.String> userIds = criteria.getUserIds();
        if (userIds.isEmpty()) {
            throw new BadRequestException("USER_STATISTICS_SEARCH_NEEDS_AT_LEAST_ONE_USER");
        }
        if (criteria.getFromStatuses().isEmpty()) {
            throw new BadRequestException("USER_STATISTICS_SEARCH_NEEDS_AT_LEAST_ONE_FROM_STATUS");
        }

        if (criteria.getToStatuses().isEmpty()) {
            throw new BadRequestException("USER_STATISTICS_SEARCH_NEEDS_AT_LEAST_ONE_TO_STATUS");
        }

        if (criteria.getSince() == null) {
            throw new BadRequestException("USER_STATISTICS_SEARCH_NEEDS_SINCE_DATE");
        }
        if (!criteria.getUpTo().after(criteria.getSince())) {
            throw new BadRequestException("USER_STATISTICS_SEARCH_UPTO_DATE_NEEDS_TO_BE_AFTER_SINCE_DATE");
        }
        if (criteria.getGranularity() == null) {
            throw new BadRequestException("USER_STATISTICS_SEARCH_NEEDS_GRANULARITY");
        }
        Map<java.lang.String, List<Date>> statisticalEventTimesByUser = userOwnerStatusChangeStatisticsDAO.getStatisticalEventTimesByUser(userIds, criteria.getFromStatuses(), criteria.getToStatuses(), criteria.getSince(), criteria.getUpTo());

        List<Date> frameStarts = new ArrayList<>();
        Date pointer = criteria.getSince();
        while (pointer.before(criteria.getUpTo())) {
            frameStarts.add(pointer);
            pointer = Date.from(pointer.toInstant().plus(criteria.getGranularity()));
        }

        List<UserOwnerStatusChangeStatistics> result = new ArrayList<>();
        for (java.lang.String userId : userIds) {
            List<UserOwnerStatusChangeStatisticsFrame> frames = new ArrayList<>();
            for (int i = 0; i < frameStarts.size(); i++) {
                Date frameStart = frameStarts.get(i);
                Date frameEnd = (i + 1) >= frameStarts.size() ? criteria.getUpTo() : new Date(frameStarts.get(i + 1).getTime() - 1);
                long count = statisticalEventTimesByUser.getOrDefault(userId, Collections.emptyList()).stream().filter(date -> !date.before(frameStart) && !date.after(frameEnd)).map(Date::getTime).count();
                frames.add(new UserOwnerStatusChangeStatisticsFrame(frameStart, count));
            }
            result.add(new UserOwnerStatusChangeStatistics(userId, frames));
        }
        return result;
    }

    public UserStatisticsPrepData getPrepData() {
        return new UserStatisticsPrepData(
                userDAO.getAllUsers().stream().map(UserMinimal::new).collect(Collectors.toList()),
                ownerStatusService.getPossibleOwnerStatusIds()
        );
    }
}
