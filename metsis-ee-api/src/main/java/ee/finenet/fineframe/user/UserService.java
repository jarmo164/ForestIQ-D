package ee.finenet.fineframe.user;

import java.util.List;
import java.util.Optional;

public interface UserService {
    Optional<User> findById(String userId);

    void activateTotp(String userId, String totpSecret);

    List<MaintainableUser> getAllUsers();

    void setUserPrivileges(String userId, List<String> givenPrivileges);

    void deleteUser(String userId);

    void addUser(MaintainableUser user, String passwordHash);

    void changeUsersPasswordHash(String userId, String newPasswordHash);
}
