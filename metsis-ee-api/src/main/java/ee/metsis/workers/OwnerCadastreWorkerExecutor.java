package ee.metsis.workers;

import ee.metsis.ownercadastre.worker.OwnerCadastreWorker;

import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

public class OwnerCadastreWorkerExecutor {

    private final ScheduledExecutorService executor = Executors.newScheduledThreadPool(1);
    private final OwnerCadastreWorker ownerCadastreWorker;

    public OwnerCadastreWorkerExecutor(OwnerCadastreWorker ownerCadastreWorker) {
        this.ownerCadastreWorker = ownerCadastreWorker;
    }

    public void run() {
        executor.scheduleAtFixedRate(ownerCadastreWorker, 0, 1, TimeUnit.DAYS);
    }
}
