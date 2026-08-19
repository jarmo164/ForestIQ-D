package ee.metsis.security.token;

import ee.finenet.fineframe.http.AbstractRequestHandler;
import ee.finenet.fineframe.http.RequestMethod;
import ee.finenet.fineframe.http.Requestable;
import ee.finenet.fineframe.security.AuthenticationService;
import ee.finenet.fineframe.security.token.EncodedToken;
import ee.finenet.fineframe.security.token.EncodedTokens;
import ee.finenet.fineframe.security.token.Jwt;
import ee.finenet.fineframe.security.token.Tokens;
import ee.metsis.ServiceRegistry;
import ee.metsis.security.Privilege;
import ee.metsis.ServiceRegistry;
import ee.metsis.security.Privilege;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import spark.Request;
import spark.Response;

import java.util.Collection;

@Requestable(value = "/token-refresh", method = RequestMethod.POST)
public class TokenRefreshRequestHandler extends AbstractRequestHandler {

    private static final Logger logger = LoggerFactory.getLogger(TokenRefreshRequestHandler.class);

    private final AuthenticationService authenticationService;
    private final Jwt jwt;

    public TokenRefreshRequestHandler(ServiceRegistry serviceRegistry) {
        this.authenticationService = serviceRegistry.getAuthenticationService();
        this.jwt = serviceRegistry.getJwt();
    }

    @Override
    public EncodedTokens handleRequest(Request req, Response res) {
        String userId = getAuthToken(req).getUserId();
        Tokens tokens = authenticationService.releaseNewTokens(userId);

        EncodedTokens encodedTokens = new EncodedTokens(
                new EncodedToken(jwt.encode(tokens.getActualToken())),
                new EncodedToken(jwt.encode(tokens.getRefreshToken())));

        logger.info("Tokens refreshed for user '{}'", userId);
        return encodedTokens;
    }

    @Override
    protected Collection<String> requireAtLeastOneOfPrivileges() {
        return privileges(Privilege.TOKEN_REFRESH.name());
    }
}
