package ee.metsis.ownercadastre.worker;

import ee.metsis.ownercadastre.api.ExternalOwnerApiOwner;
import ee.metsis.ownercadastre.api.OwnerCadastreApi;
import ee.metsis.owners.OwnerService;
import ee.metsis.workers.LastOwnersUpdateDao;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.LocalDateTime;
import java.util.List;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicLong;
import java.util.stream.Collectors;

public class OwnerCadastreWorker implements Runnable {

    private static final Logger logger = LoggerFactory.getLogger(OwnerCadastreWorker.class);

    private final OwnerCadastreApi ownerCadastreApi;
    private final OwnerService ownerService;
    private final LastOwnersUpdateDao lastOwnersUpdateDao;

    public OwnerCadastreWorker(
            OwnerCadastreApi ownerCadastreApi,
            OwnerService ownerService,
            LastOwnersUpdateDao lastOwnersUpdateDao) {
        this.ownerCadastreApi = ownerCadastreApi;
        this.ownerService = ownerService;
        this.lastOwnersUpdateDao = lastOwnersUpdateDao;
    }

    @Override
    public void run() {
        if (!ownerCadastreApi.isEnabled()) {
            logger.info("It's Owner Cadastre Worker run time, but will do nothing as Simo API is disabled.");
            return;
        }
        logger.info("Starting daily owner-cadastre work");
        final AtomicLong progression = new AtomicLong(0);
        try {
            LocalDateTime updateTime = lastOwnersUpdateDao.getLastUpdate();
            if (updateTime != null) {
                updateTime = updateTime.minusDays(1);
            }
            int step = 10000;
            int skip = 0;
            AtomicBoolean hadAnswer = new AtomicBoolean(false);
            do {
                hadAnswer.set(false);
                AtomicInteger failedInARow = new AtomicInteger(0);
                ownerCadastreApi.downloadOwnersAndExecuteOnEachOwner(
                        skip, step,
                        updateTime == null ? null : updateTime.toLocalDate(),
                        (ownerRow) -> {
                            hadAnswer.set(true);
                            try {
                                List<String> cadastreNos = ownerRow.getActiveOwnings().stream().map(
                                        aO -> aO.getCadastreNo().trim()).collect(Collectors.toList());
                                ExternalOwnerApiOwner o = ownerRow.getOwner();
                                if (!ownerService.findOwner(o.getCode()).isPresent()) {
                                    ownerService.addNewOwner(
                                            o.getCode(),
                                            o.getName(),
                                            o.getType().equals("COMPANY") ? "FIRMA" : "ERAISIK",
                                            null
                                    );
                                }
                                ownerService.registerUnknownAddedOwnings(cadastreNos);
                                ownerService.updateOwnerOwnings(o.getCode().trim(), cadastreNos);
                                failedInARow.set(0);
                                long currentProgression = progression.incrementAndGet();
                                if (currentProgression % 100 == 0) {
                                    logger.info("Daily owner-cadastre work progression: " + currentProgression);
                                }
                            } catch (Exception e) {
                                if (failedInARow.incrementAndGet() > 3) {
                                    throw new RuntimeException("More than 3 failured in a row");
                                }
                                logger.error("Owner " + ownerRow.getOwner().getCode() + " " + ownerRow.getOwner().getName() + " failed", e);
                            }
                            return null;
                        });
                skip += step;
            } while (hadAnswer.get());
            logger.info("Daily owner-cadastre work progression: " + progression.incrementAndGet() + ", FINISHED!");
            lastOwnersUpdateDao.updateLastUpdate();
        } catch (Exception e) {
            logger.error("Daily owner-cadastre work failed", e);
        }

    }

}
