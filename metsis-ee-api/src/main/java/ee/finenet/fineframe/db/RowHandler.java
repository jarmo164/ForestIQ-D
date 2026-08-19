package ee.finenet.fineframe.db;

import java.sql.ResultSet;

public interface RowHandler<T> {
    T handle(ResultSet rs);
}
