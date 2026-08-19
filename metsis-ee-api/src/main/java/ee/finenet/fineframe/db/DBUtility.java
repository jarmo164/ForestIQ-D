package ee.finenet.fineframe.db;

import java.sql.Timestamp;
import java.util.Date;

public class DBUtility {

    public static Date fromSqlToUtilDate(java.sql.Date given) {
        return given == null ? null : new Date(given.getTime());
    }

    public static Date fromSqlToUtilDate(Timestamp given) {
        return given == null ? null : new Date(given.getTime());
    }


    public static java.sql.Date fromUtiltoSqlDate(Date given) {
        return given == null ? null : new java.sql.Date(given.getTime());
    }

    public static Timestamp fromUtiltoSqlTimestamp(Date given) {
        return given == null ? null : new Timestamp(given.getTime());
    }

    public static String createQMarks(int count) {
        StringBuilder sb = new StringBuilder();
        for (int i = 1; i <= count; i++) {
            sb.append("?");
            if (i != count) {
                sb.append(",");
            }
        }
        return sb.toString();
    }

    public static String likeParam(String given) {
        if (given == null) {
            return null;
        }
        return "%" + given + "%";
    }


    public static String likeStartsWith(String given) {
        if (given == null) {
            return null;
        }
        return given + "%";
    }
}
