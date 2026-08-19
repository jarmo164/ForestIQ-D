package ee.finenet.fineframe.security.token;

import ee.finenet.fineframe.exceptions.ForbiddenException;
import ee.finenet.fineframe.http.RequestUtility;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import spark.Filter;
import spark.Request;
import spark.Response;

public class AuthTokenValidationFilter implements Filter {

    private static final Logger logger = LoggerFactory.getLogger(ee.finenet.fineframe.security.token.AuthTokenValidationFilter.class);

    public static final String ATTR_AUTH_TOKEN = "authToken";

    private final Jwt jwt;

    public AuthTokenValidationFilter(Jwt jwt) {
        this.jwt = jwt;
    }

    @Override
    public void handle(Request req, Response res) {
        String suppliedToken = RequestUtility.getAuthTokenFromHeader(req);
        if (suppliedToken.isEmpty()) {
            throw new ForbiddenException(ForbiddenException.CODE_AUTH_FAIL_NO_TOKEN);
        }
        AuthToken authToken = jwt.decodeAndValidate(suppliedToken);
        logger.info("USER: {}, IP: {}, ACTION: {} {}", authToken.getUserId(), req.ip(), req.requestMethod(), req.pathInfo());
        req.attribute(ATTR_AUTH_TOKEN, authToken);
    }
}
