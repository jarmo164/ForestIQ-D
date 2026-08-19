package ee.metsis.owners.logservice;

import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.stream.Stream;

public class OwnerLogService {

    private final ExecutorService executorService = Executors.newFixedThreadPool(10);

    private final OwnerLogDao ownerLogDao;

    public OwnerLogService(OwnerLogDao ownerLogDao) {
        this.ownerLogDao = ownerLogDao;
    }

    public Long writeLog(LogMessage logMessage) {
        return ownerLogDao.saveLogMessage(logMessage);
    }

    public void writeLogAsync(Stream<LogMessage> messages) {
        executorService.execute(() -> messages.forEach(this::writeLog));
    }

    public List<LogMessage> getOwnersWorkLog(String ownerId, Long sinceId) {
        return ownerLogDao.getOwnersWorkLog(ownerId, sinceId);
    }
}
