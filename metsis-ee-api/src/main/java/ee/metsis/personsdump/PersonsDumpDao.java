package ee.metsis.personsdump;

import ee.finenet.fineframe.db.AbstractDAO;

import java.util.List;

import javax.sql.DataSource;

public class PersonsDumpDao extends AbstractDAO {

    public PersonsDumpDao(DataSource ds) {
        super(ds);
    }

    public List<PersonsDumpEntry> findAll() {
        return queryForList("select * from persons_dump where 1=1 order by name", rs ->
            new PersonsDumpEntry(
                    getLong("id", rs),
                    getString("source", rs),
                    getString("name", rs),
                    getString("phone", rs),
                    getString("address", rs),
                    getString("code", rs)
            ));
    }

    public void addEntry(NewPersonsDumpEntry entry) {
        update("insert into persons_dump (code, name, phone, address) values (?,?,?,?)",
                entry.getCode(),
                entry.getName(),
                entry.getPhone(),
                entry.getAddress());
    }

    public void deleteEntry(Long id) {
        update("delete from persons_dump where id = ?", id);
    }
}
