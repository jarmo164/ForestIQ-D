package ee.finenet.fineframe.http;

import spark.Request;
import spark.Response;

public interface RequestHandler<T> {
    T handle(Request req, Response res);
}
