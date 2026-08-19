package ee.finenet.fineframe.db;

import org.apache.commons.dbutils.QueryRunner;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Objects;

import javax.sql.DataSource;

public class AbstractDAO {
    private final QueryRunner qr;

    public AbstractDAO(DataSource ds) {
        Objects.requireNonNull(ds, "AbstractDAO.dataSource may not be null");
        this.qr = new QueryRunner(ds);
    }

    protected <T> T queryForOne(String query, RowHandler<T> handler, Object... params) {
        try {
            return qr.query(query, rs -> {
                if (rs.next()) {
                    return handler.handle(rs);
                }
                return null;
            }, params);
        } catch (SQLException e) {
            throw new DatabaseException(e);
        }
    }

    protected <T> List<T> queryForList(String query, RowHandler<T> handler, Object... params) {
        try {
            return qr.query(query, rs -> {
                List<T> result = new ArrayList<>();
                while (rs.next()) {
                    result.add(handler.handle(rs));
                }
                return result;
            }, params);
        } catch (SQLException e) {
            throw new DatabaseException(e);
        }
    }

    protected <T> T insert(String query, RowHandler<T> handler, Object... params) {
        try {
            return qr.insert(query, rs -> {
                if (rs.next()) {
                    return handler.handle(rs);
                }
                return null;
            }, params);
        } catch (SQLException e) {
            throw new DatabaseException(e);
        }
    }

    protected void update(String query, Object... params) {
        try {
            qr.update(query, params);
        } catch (SQLException e) {
            throw new DatabaseException(e);
        }
    }

    protected String getString(String key, ResultSet rs) {
        try {
            return rs.getString(key);
        } catch (SQLException e) {
            throw new DatabaseException(e);
        }
    }

    protected Double getDouble(String key, ResultSet rs) {
        try {
            return rs.getDouble(key);
        } catch (SQLException e) {
            throw new DatabaseException(e);
        }
    }

    protected Boolean getBoolean(String key, ResultSet rs) {
        try {
            return rs.getBoolean(key);
        } catch (SQLException e) {
            throw new DatabaseException(e);
        }
    }

    protected Long getLong(String key, ResultSet rs) {
        try {
            return rs.getLong(key);
        } catch (SQLException e) {
            throw new DatabaseException(e);
        }
    }

    protected Integer getInt(String key, ResultSet rs) {
        try {
            return rs.getInt(key);
        } catch (SQLException e) {
            throw new DatabaseException(e);
        }
    }

    protected Date getTime(String key, ResultSet rs) {
        try {
            return DBUtility.fromSqlToUtilDate(rs.getTimestamp(key));
        } catch (SQLException e) {
            throw new DatabaseException(e);
        }
    }

    protected byte[] getBytes(String key, ResultSet rs) {
        try {
            return rs.getBytes(key);
        } catch (SQLException e) {
            throw new DatabaseException(e);
        }
    }

}
