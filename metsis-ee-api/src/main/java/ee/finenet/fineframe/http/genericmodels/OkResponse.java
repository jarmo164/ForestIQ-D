package ee.finenet.fineframe.http.genericmodels;

public class OkResponse {

    public static final ee.finenet.fineframe.http.genericmodels.OkResponse INSTANCE = new ee.finenet.fineframe.http.genericmodels.OkResponse();

    private final String message = "OK";

    private OkResponse() {}

    public String getMessage() {
        return message;
    }
}
