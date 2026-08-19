package ee.metsis.other;

import ee.finenet.fineframe.http.AbstractRequestHandler;
import ee.finenet.fineframe.http.Requestable;
import ee.finenet.fineframe.http.genericmodels.OkResponse;
import ee.metsis.ServiceRegistry;
import spark.Request;
import spark.Response;

import java.util.Collection;

@Requestable("/status")
public class StatusRequestHandler extends AbstractRequestHandler {

    public StatusRequestHandler(ServiceRegistry serviceRegistry) {
    }

    @Override
    protected Object handleRequest(Request req, Response res) {
        return OkResponse.INSTANCE;
    }

    @Override
    protected Collection<String> requireAtLeastOneOfPrivileges() {
        return noPrivilegesRequired();
    }
}
