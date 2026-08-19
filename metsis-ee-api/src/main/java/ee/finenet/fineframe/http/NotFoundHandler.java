package ee.finenet.fineframe.http;

import ee.finenet.fineframe.http.genericmodels.ErrorModel;
import ee.finenet.fineframe.security.token.AuthToken;
import org.eclipse.jetty.http.HttpStatus;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import spark.Request;
import spark.Response;

import static ee.finenet.fineframe.security.token.AuthTokenValidationFilter.ATTR_AUTH_TOKEN;

public class NotFoundHandler implements RequestHandler<ErrorModel> {

    private static final Logger logger = LoggerFactory.getLogger(ee.finenet.fineframe.http.NotFoundHandler.class);

    @Override
    public NotFoundResponse handle(Request req, Response res) {
        AuthToken authToken = req.attribute(ATTR_AUTH_TOKEN);
        if (authToken == null) {
            logger.info("Unauthenticated user tried to access non-existent path {}", req.pathInfo());
        } else {
            logger.info("User {} tried to access non-existent path {}", authToken.getUserId(), req.pathInfo());
        }
        res.status(HttpStatus.NOT_FOUND_404);
        return NotFoundResponse.NOT_FOUND;
    }

    static class NotFoundResponse extends ErrorModel {

        static NotFoundResponse NOT_FOUND = new NotFoundResponse();

        private NotFoundResponse() {
            super("SERVICE_NOT_FOUND", "Requested service was not found");
        }
    }
}
