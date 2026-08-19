package ee.finenet.fineframe.db;

import org.postgresql.ds.PGPoolingDataSource;

import javax.sql.DataSource;

public class PgDatasourceFactory implements DatasourceFactory {

    private PGPoolingDataSource dataSource;

    @Override
    public synchronized DataSource getInstance(DatabaseConfiguration conf) {
        if (this.dataSource == null) {
            this.dataSource = new PGPoolingDataSource();
            this.dataSource.setUrl(conf.getUrl());
            this.dataSource.setUser(conf.getUser());
            this.dataSource.setPassword(conf.getPassword());
        }
        return this.dataSource;
    }
}
