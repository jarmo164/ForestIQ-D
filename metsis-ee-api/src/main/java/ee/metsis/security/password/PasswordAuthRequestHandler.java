package ee.metsis.security.password;

import ee.finenet.fineframe.exceptions.ForbiddenException;
import ee.finenet.fineframe.http.Headers;
import ee.finenet.fineframe.http.RequestHandler;
import ee.finenet.fineframe.http.RequestMethod;
import ee.finenet.fineframe.http.Requestable;
import ee.finenet.fineframe.security.AuthenticationService;
import ee.finenet.fineframe.security.token.AuthToken;
import ee.finenet.fineframe.security.token.EncodedToken;
import ee.finenet.fineframe.security.token.Jwt;
import ee.finenet.fineframe.user.User;
import ee.finenet.fineframe.user.UserService;
import ee.metsis.ServiceRegistry;
import ee.metsis.ServiceRegistry;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import spark.Request;
import spark.Response;

import static ee.finenet.fineframe.exceptions.ForbiddenException.CODE_AUTH_FAIL_NO_SUCH_USER;

@Requestable(value = "/password-login", secured = false, method = RequestMethod.POST)
public class PasswordAuthRequestHandler implements RequestHandler {

    private static final Logger logger = LoggerFactory.getLogger(PasswordAuthRequestHandler.class);

    private final AuthenticationService authenticationService;
    private final UserService userService;
    private final Jwt tokenEncoder;

    public PasswordAuthRequestHandler(ServiceRegistry serviceRegistry) {
        this.authenticationService = serviceRegistry.getAuthenticationService();
        this.userService = serviceRegistry.getUserService();
        this.tokenEncoder = serviceRegistry.getJwt();
    }

    @Override
    public EncodedToken handle(Request req, Response res) {
        ee.finenet.fineframe.security.password.UserPasswordRequestModel credentials = Headers.parseBasicAuth(req);
        String remoteIp = req.ip();
        String suppliedUsername = credentials.getUser();
        User user = userService.findById(credentials.getUser())
                .orElseThrow(() -> new ForbiddenException(CODE_AUTH_FAIL_NO_SUCH_USER, String.format("User '%s' does not exist", suppliedUsername)));
        AuthToken authToken = authenticationService.logInWithPasswordAndReleaseTotpToken(user, credentials);
        String token = tokenEncoder.encode(authToken);
        logger.info("PASSWORD AUTH SUCCESS; USER: '{}'; IP: '{}'", suppliedUsername, remoteIp);
        return new EncodedToken(token);
    }
}
