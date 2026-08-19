package ee.finenet.fineframe.security.password;

public interface PasswordHandler {

    String hashPassword(String password);

    boolean checkPassword(String candidate, String hash);

    boolean isPasswordSuitable(String candidate);

    String createRandomPassword();

}
