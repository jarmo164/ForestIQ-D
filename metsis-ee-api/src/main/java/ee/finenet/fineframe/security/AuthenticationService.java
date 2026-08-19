package ee.finenet.fineframe.security;

import ee.finenet.fineframe.exceptions.BadRequestException;
import ee.finenet.fineframe.exceptions.ForbiddenException;
import ee.finenet.fineframe.security.password.ChangePasswordModel;
import ee.finenet.fineframe.security.password.PasswordHandler;
import ee.finenet.fineframe.security.password.UserPasswordRequestModel;
import ee.finenet.fineframe.security.token.AuthToken;
import ee.finenet.fineframe.security.token.TokenService;
import ee.finenet.fineframe.security.token.Tokens;
import ee.finenet.fineframe.security.totp.TotpHandler;
import ee.finenet.fineframe.user.User;
import ee.finenet.fineframe.user.UserService;

import java.util.Objects;

import static ee.finenet.fineframe.exceptions.BadRequestException.CODE_CHANGE_MY_PASSWORD_NEW_PASSWORD_INVALID;
import static ee.finenet.fineframe.exceptions.BadRequestException.CODE_CHANGE_MY_PASSWORD_NEW_PASSWORD_NEW_PASSWORD_AGAIN_MISMATCH;
import static ee.finenet.fineframe.exceptions.BadRequestException.CODE_CHANGE_MY_PASSWORD_WRONG_OLD_PASSWORD;
import static ee.finenet.fineframe.exceptions.ForbiddenException.CODE_AUTH_FAILED_TOTP_OFF;
import static ee.finenet.fineframe.exceptions.ForbiddenException.CODE_AUTH_FAILED_WRONG_TOTP_CODE;
import static ee.finenet.fineframe.exceptions.ForbiddenException.CODE_AUTH_FAIL_NO_SUCH_USER;
import static ee.finenet.fineframe.exceptions.ForbiddenException.CODE_AUTH_FAIL_WRONG_PASSWORD;

public class AuthenticationService {

    private final UserService userService;
    private final TokenService tokenService;
    private final PasswordHandler passwordHandler;
    private final boolean isDevMode;

    public AuthenticationService(UserService userService, TokenService tokenService, PasswordHandler passwordHandler, boolean isDevMode) {
        Objects.requireNonNull(userService, "AuthenticationService.userService may not be null");
        Objects.requireNonNull(tokenService, "AuthenticationService.tokenService may not be null");
        Objects.requireNonNull(passwordHandler, "AuthenticationService.passwordHandler may not be null");
        this.userService = userService;
        this.tokenService = tokenService;
        this.passwordHandler = passwordHandler;
        this.isDevMode = isDevMode;
    }

    public AuthToken logInWithPasswordAndReleaseTotpToken(User user, UserPasswordRequestModel suppliedCredentials) {
        if (!passwordHandler.checkPassword(suppliedCredentials.getPassword(), user.getPasswordHash())) {
            throw new ForbiddenException(CODE_AUTH_FAIL_WRONG_PASSWORD, String.format("Wrong password supplied for user '%s'", user.getId()));
        }
        if (!user.isTotpEnabled()) {
            return tokenService.createTotpRegistrationToken(user.getId(), user.getName());
        }
        return tokenService.createTotpToken(user.getId(), user.getName());
    }

    public Tokens logInWithTotpCode(Long totpCode, User user) {
        String userId = user.getId();
        if (!isDevMode) {
            if (!user.isTotpEnabled()) {
                throw new ForbiddenException(CODE_AUTH_FAILED_TOTP_OFF);
            }
            if (!TotpHandler.isCorrectTOTPCode(user.getTotpSecret(), totpCode)) {
                throw new ForbiddenException(CODE_AUTH_FAILED_WRONG_TOTP_CODE);
            }
        }

        return releaseNewTokens(userId);
    }

    public Tokens releaseNewTokens(String userId) {
        User user = userService.findById(userId).orElseThrow(() -> new ForbiddenException(CODE_AUTH_FAIL_NO_SUCH_USER));
        return new Tokens(
                tokenService.createFullToken(userId, user.getName(), user.getPrivileges()),
                tokenService.createRefreshToken(userId, user.getName()));
    }

    public void enableTotp(String userId, String totpSecret, Long totpCode) {
        if (!TotpHandler.isCorrectTOTPCode(totpSecret, totpCode)) {
            throw new ForbiddenException(CODE_AUTH_FAILED_WRONG_TOTP_CODE);
        }
        userService.activateTotp(userId, totpSecret);
    }

    public void changeUsersPassword(String userId, ChangePasswordModel changePasswordModel) {
        assertChangePasswordModelValid(userId, changePasswordModel);
        userService.changeUsersPasswordHash(userId, passwordHandler.hashPassword(changePasswordModel.getNewPassword()));
    }

    private void assertChangePasswordModelValid(String userId, ChangePasswordModel changePasswordModel) {
        if (userId == null) {
            throw new BadRequestException(CODE_AUTH_FAIL_NO_SUCH_USER);
        }
        String passwordHash = userService.findById(userId).orElseThrow(() -> new BadRequestException(CODE_AUTH_FAIL_NO_SUCH_USER)).getPasswordHash();
        if (changePasswordModel == null) {
            throw new BadRequestException(CODE_CHANGE_MY_PASSWORD_WRONG_OLD_PASSWORD);
        }
        String oldPassword = changePasswordModel.getOldPassword();
        if (oldPassword == null) {
            throw new BadRequestException(CODE_CHANGE_MY_PASSWORD_WRONG_OLD_PASSWORD);
        }
        if (!passwordHandler.checkPassword(oldPassword, passwordHash)) {
            throw new BadRequestException(CODE_CHANGE_MY_PASSWORD_WRONG_OLD_PASSWORD);
        }
        String newPasswordCandidate = changePasswordModel.getNewPassword();
        if (newPasswordCandidate == null || !passwordHandler.isPasswordSuitable(newPasswordCandidate)) {
            throw new BadRequestException(CODE_CHANGE_MY_PASSWORD_NEW_PASSWORD_INVALID);
        }
        if (!newPasswordCandidate.equals(changePasswordModel.getNewPasswordAgain())) {
            throw new BadRequestException(CODE_CHANGE_MY_PASSWORD_NEW_PASSWORD_NEW_PASSWORD_AGAIN_MISMATCH);
        }
    }
}
