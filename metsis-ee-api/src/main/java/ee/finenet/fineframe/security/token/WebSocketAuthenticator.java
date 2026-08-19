package ee.finenet.fineframe.security.token;

import ee.finenet.fineframe.exceptions.BadRequestException;
import org.eclipse.jetty.websocket.api.Session;

public class WebSocketAuthenticator {

    private final Jwt jwt;

    public WebSocketAuthenticator(Jwt jwt) {
        this.jwt = jwt;
    }

    public AuthToken authenticate(Session session) {
        String tokenString = getTokenString(session);
        return jwt.decodeAndValidate(tokenString);
    }

    private String getTokenString(Session session) {
        try {
            return session.getUpgradeRequest().getParameterMap().get("token").get(0);
        } catch (Exception e) {
            throw new BadRequestException("Websocket requests must have token as a request parameter");
        }
    }
}
