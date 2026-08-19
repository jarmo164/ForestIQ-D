package ee.finenet.fineframe.security.password;

import org.mindrot.jbcrypt.BCrypt;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.math.BigInteger;
import java.security.SecureRandom;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public class BCryptBasedPasswordHandler implements PasswordHandler {

    private static final Logger logger = LoggerFactory.getLogger(ee.finenet.fineframe.security.password.BCryptBasedPasswordHandler.class);

    private SecureRandom random = new SecureRandom();

    @Override
    public String hashPassword(String password) {
        return BCrypt.hashpw(password, BCrypt.gensalt());
    }

    @Override
    public boolean checkPassword(String candidate, String hash) {
        try {
            return BCrypt.checkpw(candidate, hash);
        } catch (Exception e) {
            logger.warn("Something went wrong with verifying a password", e);
            return false;
        }
    }

    @Override
    public boolean isPasswordSuitable(String candidate) {
        return candidate != null &&
                candidate.length() >= 8 &&
                !candidate.toLowerCase().equals(candidate) &&
                !candidate.toUpperCase().equals(candidate) &&
                containsAtLeastOneNumber(candidate);
    }

    @Override
    public String createRandomPassword() {
        String startingPoint = createRandomString().toUpperCase() + createRandomString();
        List<Character> characters = new ArrayList<>();
        for (char c : startingPoint.toCharArray()) {
            characters.add(c);
        }
        Collections.shuffle(characters);
        StringBuilder result = new StringBuilder();
        for (Character character : characters) {
            result.append(character);
        }
        return result.toString();
    }

    private String createRandomString() {
        return new BigInteger(35, random).toString(32);
    }

    private boolean containsAtLeastOneNumber(String candidate) {
        for (char c : candidate.toCharArray()) {
            if (c == '0' || c == '1' || c == '2' || c == '3' || c == '4' || c == '5' || c == '6' || c == '7' || c == '8'
                    || c == '9') {
                return true;
            }
        }
        return false;
    }
}
