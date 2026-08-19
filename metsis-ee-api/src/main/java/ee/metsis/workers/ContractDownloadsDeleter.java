package ee.metsis.workers;

import ee.metsis.contracts.ContractService;

import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

public class ContractDownloadsDeleter {

    private final ScheduledExecutorService executor = Executors.newScheduledThreadPool(1);

    private final ContractService contractService;

    public ContractDownloadsDeleter(ContractService contractService) {
        this.contractService = contractService;
    }

    public void run() {
        executor.scheduleAtFixedRate(contractService::deleteExpiredDownloads, 0, 120000, TimeUnit.MILLISECONDS);
    }
}
