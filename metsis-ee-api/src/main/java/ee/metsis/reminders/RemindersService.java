package ee.metsis.reminders;

import ee.finenet.fineframe.exceptions.BadRequestException;
import ee.finenet.fineframe.user.UserMinimal;
import ee.finenet.fineframe.utilities.DateUtility;
import ee.finenet.fineframe.utilities.StringUtility;
import ee.metsis.owners.Owner;
import ee.metsis.owners.OwnerService;
import ee.metsis.owners.logservice.LogMessage;
import ee.metsis.owners.logservice.OwnerLogService;

import java.util.List;
import java.util.Optional;

public class RemindersService {
    private final RemindersDao remindersDao;
    private final OwnerService ownerService;
    private final OwnerLogService ownerLogService;

    public RemindersService(RemindersDao remindersDao, OwnerService ownerService, OwnerLogService ownerLogService) {
        this.remindersDao = remindersDao;
        this.ownerService = ownerService;
        this.ownerLogService = ownerLogService;
    }

    public List<Reminder> getReminders(String creator) {
        return remindersDao.getMyReminders(creator);
    }

    public List<Reminder> getFutureReminders(List<String> creators) {
        return remindersDao.getFutureReminders(creators);
    }

    public void addReminder(Reminder reminder, String creator) {
        if (StringUtility.isNullOrBlank(reminder.getText())) {
            throw new BadRequestException("REMINDER_EMPTY_TEXT_NOT_ALLOWED");
        }
        reminder.setText(StringUtility.trimToEmpty(reminder.getText()));
        if (reminder.getText().length() > 500) {
            throw new BadRequestException("REMINDER_TEXT_TOO_LONG");
        }
        if (reminder.getDueTime() == null) {
            throw new BadRequestException("REMINDER_EMPTY_DUE_TIME_NOT_ALLOWED");
        }
        String ownerId = reminder.getOwnerId();
        if (!StringUtility.isNullOrBlank(ownerId)) {
            Optional<Owner> owner = ownerService.findOwner(ownerId);
            if (!owner.isPresent()) {
                throw new BadRequestException("REMINDER_OWNER_WITH_GIVEN_ID_DOES_NOT_EXIST");
            }
            LogMessage log = new LogMessage();
            log.setCreator(creator);
            log.setTimestamp(System.currentTimeMillis());
            log.setOwner(ownerId);
            log.setOwnersAssignee(owner.map(Owner::getAssignee).map(UserMinimal::getId).orElse(null));
            log.setMessage(String.format("Reminder:\n%s\n\nDue time:\n%s", reminder.getText(), DateUtility.formatSimpleDate(reminder.getDueTime())));
            ownerLogService.writeLog(log);
        }
        String cadastreNo = reminder.getCadastre();
        if (cadastreNo != null) {
            reminder.setCadastre(cadastreNo);
            ownerService.findCadastre(cadastreNo).ifPresent(cadastre -> reminder.setPropertyName(cadastre.getName()));
        }
        remindersDao.addReminder(reminder, creator);
    }

    public void deleteReminder(Long id) {
        remindersDao.deleteReminder(id);
    }
}
