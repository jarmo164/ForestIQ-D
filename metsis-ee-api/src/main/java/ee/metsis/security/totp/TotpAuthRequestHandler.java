package ee.metsis.security.totp;

import ee.finenet.fineframe.exceptions.ForbiddenException;
import ee.finenet.fineframe.exceptions.UnexpextedException;
import ee.finenet.fineframe.http.AbstractRequestHandler;
import ee.finenet.fineframe.http.RequestMethod;
import ee.finenet.fineframe.http.Requestable;
import ee.finenet.fineframe.security.AuthenticationService;
import ee.finenet.fineframe.security.token.*;
import ee.finenet.fineframe.security.totp.TotpLoginRequestModel;
import ee.finenet.fineframe.serialization.GsonHolder;
import ee.finenet.fineframe.user.User;
import ee.finenet.fineframe.user.UserService;
import ee.metsis.ServiceRegistry;
import ee.metsis.security.Privilege;
import ee.metsis.ServiceRegistry;
import ee.metsis.security.Privilege;
import spark.Request;
import spark.Response;

import java.util.Collection;

import static ee.finenet.fineframe.exceptions.ForbiddenException.CODE_AUTH_FAILED_WRONG_TOTP_CODE;
import static ee.finenet.fineframe.exceptions.ForbiddenException.CODE_AUTH_FAIL_NO_SUCH_USER;

@Requestable(value = "/totp", method = RequestMethod.POST)
public class TotpAuthRequestHandler extends AbstractRequestHandler {

    private final AuthenticationService authenticationService;
    private final UserService userService;
    private final Jwt jwt;

    public TotpAuthRequestHandler(ServiceRegistry serviceRegistry) {
        this.authenticationService = serviceRegistry.getAuthenticationService();
        this.userService = serviceRegistry.getUserService();
        this.jwt = serviceRegistry.getJwt();
    }

    @Override
    protected Object handleRequest(Request req, Response res) {
        AuthToken authToken = getAuthToken(req);
        String userId = authToken.getUserId();
        String body = req.body();
        TotpLoginRequestModel reqModel = GsonHolder.GSON.fromJson(body, TotpLoginRequestModel.class);
        User user = userService.findById(userId).orElseThrow(() -> new ForbiddenException(CODE_AUTH_FAIL_NO_SUCH_USER));
        assertRequestValid(reqModel);
        Long totpCode = reqModel.getTotpCode();

        if (!user.isTotpEnabled()) {
            String totpSharedSecret = authToken.getTotpSharedSecret();
            if (totpSharedSecret == null) {
                throw new UnexpextedException("2FA is not enabled but somehow user managed to pass valid token without totp shared secret");
            }
            authenticationService.enableTotp(userId, totpSharedSecret, totpCode);
            user = userService.findById(userId).orElseThrow(() -> new ForbiddenException(CODE_AUTH_FAIL_NO_SUCH_USER));
        }

        Tokens tokens = authenticationService.logInWithTotpCode(totpCode, user);
        return new EncodedTokens(
                new EncodedToken(jwt.encode(tokens.getActualToken())),
                new EncodedToken(jwt.encode(tokens.getRefreshToken()))
        );
    }

    private void assertRequestValid(TotpLoginRequestModel model) {
        if (model == null || model.getTotpCode() == null) {
            throw new ForbiddenException(CODE_AUTH_FAILED_WRONG_TOTP_CODE);
        }
    }

    @Override
    protected Collection<String> requireAtLeastOneOfPrivileges() {
        return privileges(Privilege.TOTP.name());
    }


}
