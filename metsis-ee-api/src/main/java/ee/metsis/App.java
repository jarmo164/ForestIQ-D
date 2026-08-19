package ee.metsis;

import ee.finenet.fineframe.db.DatabaseConfiguration;
import ee.finenet.fineframe.db.DatasourceFactory;
import ee.finenet.fineframe.http.FineFrameBootstrap;
import ee.finenet.fineframe.security.AuthConfiguration;
import ee.metsis.configuration.AppGeneralConfiguration;
import ee.metsis.configuration.SimoApiConfiguration;
import ee.metsis.contracts.BuyerConfiguration;
import ee.metsis.workers.ContractDownloadsDeleter;
import ee.metsis.workers.OwnerCadastreWorkerExecutor;

class App {

    private final AppGeneralConfiguration appGeneralConfiguration;
    private final ServiceRegistry serviceRegistry;

    App(AppGeneralConfiguration appGeneralConfiguration,
        AuthConfiguration authConfiguration,
        DatabaseConfiguration databaseConfiguration,
        BuyerConfiguration buyerConfiguration,
        SimoApiConfiguration simoApiConfiguration,
        DatasourceFactory datasourceFactory
    ) {
        this.appGeneralConfiguration = appGeneralConfiguration;
        this.serviceRegistry = new ServiceRegistry(datasourceFactory.getInstance(databaseConfiguration),
                authConfiguration, appGeneralConfiguration, buyerConfiguration, simoApiConfiguration);
    }

    void run() {
        new ContractDownloadsDeleter(serviceRegistry.getContractService()).run();
        new OwnerCadastreWorkerExecutor(serviceRegistry.getOwnerCadastreWorker()).run();
        FineFrameBootstrap.initialize(
                "ee.metsis",
                serviceRegistry,
                ServiceRegistry.class,
                serviceRegistry.getJwt(),
                appGeneralConfiguration.getPort()
        );
    }
}
