package ee.finenet.fineframe.http;

import ee.finenet.fineframe.utilities.StringUtility;
import spark.Request;

import static ee.finenet.fineframe.http.Headers.AUTHORIZATION;
import static ee.finenet.fineframe.http.Headers.TOKEN_PREFIX;

public class RequestUtility {

    public static String getAuthTokenFromHeader(Request req) {
        return StringUtility.removeSubstring(StringUtility.emptyIfNull(req.headers(AUTHORIZATION)), TOKEN_PREFIX);
    }
}
