package ee.metsis;

import ee.finenet.fineframe.configuration.PropertyLoader;
import ee.finenet.fineframe.db.DatabaseConfiguration;
import ee.finenet.fineframe.db.PgDatasourceFactory;
import ee.finenet.fineframe.security.AuthConfiguration;
import ee.metsis.configuration.AppGeneralConfiguration;
import ee.metsis.configuration.SimoApiConfiguration;
import ee.metsis.contracts.BuyerConfiguration;
import liquibase.Contexts;
import liquibase.LabelExpression;
import liquibase.Liquibase;
import liquibase.database.Database;
import liquibase.database.DatabaseFactory;
import liquibase.database.jvm.JdbcConnection;
import liquibase.resource.ClassLoaderResourceAccessor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.sql.Connection;
import java.util.Properties;

import javax.sql.DataSource;

public class AppRunner {

    private static final Logger logger = LoggerFactory.getLogger(AppRunner.class);

    public static void main(String[] args) {
        Properties properties;
        if (args.length == 0) {
            logger.info("Reading properties from classpath");
            properties = PropertyLoader.loadProperties(
                    Thread.currentThread().getContextClassLoader().getResourceAsStream(
                            "metsis.properties"
                    )
            );
        } else {
            logger.info("Reading properties from {}", args[0]);
            properties = PropertyLoader.loadProperties(args[0]);
        }
        enhancePropertiesWithEnv(properties);
        logProperties(properties);
        PgDatasourceFactory datasourceFactory = new PgDatasourceFactory();
        runLiquibase(datasourceFactory.getInstance(new DatabaseConfiguration(properties)));
        new App(
                new AppGeneralConfiguration(properties),
                new AuthConfiguration(properties),
                new DatabaseConfiguration(properties),
                new BuyerConfiguration(properties),
                new SimoApiConfiguration(properties),
                datasourceFactory
        ).run();
    }

    private static void runLiquibase(DataSource dataSource) {
        try {
            Connection connection = dataSource.getConnection();
            Database database = DatabaseFactory.getInstance().findCorrectDatabaseImplementation(new JdbcConnection(connection));

            Liquibase liquibase = new liquibase.Liquibase(
                    "changesets/db.changelog-master.yaml",
                    new ClassLoaderResourceAccessor(), database
            );

            liquibase.update(new Contexts(), new LabelExpression());
        } catch (Exception e) {
            throw new RuntimeException("Liquibase migration failed", e);
        }

    }

    private static void enhancePropertiesWithEnv(Properties properties) {
        for (Object o : properties.keySet()) {
            if (o instanceof String) {
                String key = (String) o;
                if (key.startsWith("METSIS_") || key.startsWith("FINEFRAME_")) {
                    String envValue = System.getenv(key);
                    if (envValue != null && !envValue.isEmpty()) {
                        properties.setProperty(key, envValue);
                    }
                }
            }
        }
    }

    private static void logProperties(Properties properties) {
        logger.info("Following properties are set:");
        for (Object o : properties.keySet()) {
            logger.info(o + "=" + properties.get(o));
        }
    }
}
