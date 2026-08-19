package ee.metsis.users;

import ee.finenet.fineframe.exceptions.BadRequestException;
import ee.finenet.fineframe.user.MaintainableUser;
import ee.finenet.fineframe.user.User;
import ee.finenet.fineframe.user.UserService;
import ee.metsis.owners.OwnerDAO;

import java.util.List;
import java.util.Optional;

public class MetsisEEUserService implements UserService {

    private final UserDAO userDAO;
    private final OwnerDAO ownerDAO;

    public MetsisEEUserService(UserDAO userDAO, OwnerDAO ownerDAO) {
        this.userDAO = userDAO;
        this.ownerDAO = ownerDAO;
    }

    public Optional<User> findById(String userId) {
        return userDAO.getUser(userId);
    }


    public void activateTotp(String userId, String totpSecret) {
        userDAO.activateTotp(userId, totpSecret);
    }

    public List<MaintainableUser> getAllUsers() {
        return userDAO.getAllUsers();
    }

    public void setUserPrivileges(String userId, List<String> givenPrivileges) {
        userDAO.setUserPrivileges(userId, givenPrivileges);
    }

    public void deleteUser(String userId) {
        if (!ownerDAO.getAllOwnersWithAssignee(userId).isEmpty()) {
            throw new BadRequestException("CAN_NOT_DELETE_USER_HAS_ASSIGNED_OWNERS");
        }
        userDAO.deleteUser(userId);
    }

    public void addUser(MaintainableUser user, String passwordHash) {
        userDAO.addUser(user, passwordHash);
    }

    public void changeUsersPasswordHash(String userId, String newPasswordHash) {
        userDAO.changeUsersPasswordHash(userId, newPasswordHash);
    }
}
