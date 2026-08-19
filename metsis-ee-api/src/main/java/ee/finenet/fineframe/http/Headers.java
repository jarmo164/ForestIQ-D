package ee.finenet.fineframe.http;

import ee.finenet.fineframe.exceptions.FineFrameException;
import ee.finenet.fineframe.exceptions.ForbiddenException;
import ee.finenet.fineframe.exceptions.UnauthorizedException;
import ee.finenet.fineframe.exceptions.UnexpextedException;
import ee.finenet.fineframe.security.password.UserPasswordRequestModel;
import ee.finenet.fineframe.utilities.StringUtility;
import spark.Request;

import java.nio.charset.StandardCharsets;
import java.util.Base64;

import static ee.finenet.fineframe.exceptions.ForbiddenException.CODE_AUTH_FAIL_NO_PASSWORD;
import static ee.finenet.fineframe.exceptions.ForbiddenException.CODE_AUTH_FAIL_NO_USERNAME;

public class Headers {

    public static final String AUTHORIZATION = "Authorization";
    private static final String BASIC_AUTH_PREFIX = "Basic ";
    public static final String TOKEN_PREFIX = "Bearer ";

    public static UserPasswordRequestModel parseBasicAuth(Request req) {
        String authorization = getAuthHeader(req);
        if (!authorization.startsWith(BASIC_AUTH_PREFIX)) {
            throw new UnauthorizedException();
        }
        try {
            String base64Credentials = authorization.substring(BASIC_AUTH_PREFIX.length()).trim();
            String credentials = new String(Base64.getDecoder().decode(base64Credentials), StandardCharsets.UTF_8);
            String[] values = credentials.split(":", 2);
            String user = values[0];
            String password = values[1];
            if (StringUtility.emptyIfNull(user).isEmpty()) {
                throw new ForbiddenException(CODE_AUTH_FAIL_NO_USERNAME);
            }
            if (StringUtility.emptyIfNull(password).isEmpty()) {
                throw new ForbiddenException(CODE_AUTH_FAIL_NO_PASSWORD);
            }
            return new UserPasswordRequestModel(user, password);
        } catch (Exception e) {
            if (e instanceof FineFrameException) {
                throw e;
            }
            throw new UnexpextedException("Something went wrong while attempting password authentication");
        }
    }

    private static String getAuthHeader(Request req) {
        String headerValue = StringUtility.emptyIfNull(req.headers(AUTHORIZATION)).trim();
        if (headerValue.isEmpty()) {
            throw new UnauthorizedException();
        }
        return headerValue;
    }
}
