package ee.finenet.fineframe.db;

import javax.sql.DataSource;

public interface DatasourceFactory {

    DataSource getInstance(DatabaseConfiguration databaseConfiguration);

}
