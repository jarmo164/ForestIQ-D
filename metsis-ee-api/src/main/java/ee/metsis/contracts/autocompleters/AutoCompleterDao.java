package ee.metsis.contracts.autocompleters;

import ee.finenet.fineframe.db.AbstractDAO;
import ee.finenet.fineframe.db.DBUtility;

import java.util.List;

import javax.sql.DataSource;

public class AutoCompleterDao extends AbstractDAO {
    public AutoCompleterDao(DataSource ds) {
        super(ds);
    }

    public List<String> getCadastresById(String id) {
        return queryForList("select id from cadastres where id like ? order by id limit 50", rs -> getString("id", rs),
                DBUtility.likeStartsWith(id));
    }

    public List<String> getOwnersById(String id) {
        return queryForList("select id from owners where id like ? order by id limit 50", rs -> getString("id", rs),
                DBUtility.likeStartsWith(id));
    }
}
