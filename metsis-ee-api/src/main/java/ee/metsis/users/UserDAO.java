package ee.metsis.users;

import ee.finenet.fineframe.db.AbstractDAO;
import ee.finenet.fineframe.user.MaintainableUser;
import ee.finenet.fineframe.user.User;
import ee.finenet.fineframe.user.UserMinimal;

import java.util.List;
import java.util.Optional;

import javax.sql.DataSource;

public class UserDAO extends AbstractDAO {

    public UserDAO(DataSource ds) {
        super(ds);
    }

    public Optional<User> getUser(String userId) {
        return Optional.ofNullable(queryForOne(
                "select u.id, u.fullname, u.password_hash, u.totp_secret, u.ivisible from users u where u.id = ?",
                rs -> new User(
                        getString("id", rs),
                        getString("fullname", rs),
                        getUserPrivileges(userId),
                        getString("password_hash", rs),
                        getString("totp_secret", rs),
                        getBoolean("ivisible", rs)
                ), userId));
    }

    private List<String> getUserPrivileges(String userId) {
        return queryForList(
                "select id from privileges where user_id = ?",
                rs -> getString("id", rs), userId);
    }

    public void activateTotp(String userId, String totpSecret) {
        update("update users set totp_secret = ? where id = ?", totpSecret, userId);
    }

    public List<MaintainableUser> getAllUsers() {
        return queryForList("select * from users where ivisible = false",
                rs -> {
                    String id = getString("id", rs);
                    List<String> userPrivileges = getUserPrivileges(id);
                    return new MaintainableUser(id, getString("fullname", rs), userPrivileges);
                });
    }

    private void deleteUserPrivileges(String userId) {
        update("delete from privileges where user_id = ?", userId);
    }

    public void setUserPrivileges(String userId, List<String> givenPrivileges) {
        deleteUserPrivileges(userId);
        for (String privilege : givenPrivileges) {
            update("insert into privileges (user_id, id) values (?, ?)", userId, privilege);
        }
    }

    public void deleteUser(String userId) {
        deleteUserPrivileges(userId);
        update("delete from users where id = ?", userId);
    }

    public void addUser(MaintainableUser user, String passwordHash) {
        update("insert into users (id, fullname, password_hash) values (?,?,?)", user.getId(), user.getName(), passwordHash);
    }

    public void changeUsersPasswordHash(String userId, String newPasswordHash) {
        update("update users set password_hash = ? where id = ?", newPasswordHash, userId);
    }

    public List<UserMinimal> getDistinctUserMinimals() {
        return queryForList("select distinct id, fullname from users where ivisible = false",
                rs -> new UserMinimal(getString("id", rs), getString("fullname", rs)));
    }
}
