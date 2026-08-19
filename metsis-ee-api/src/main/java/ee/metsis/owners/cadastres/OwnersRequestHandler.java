package ee.metsis.owners.cadastres;

import ee.finenet.fineframe.http.RequestHandler;
import ee.finenet.fineframe.http.Requestable;
import ee.metsis.ServiceRegistry;
import ee.metsis.owners.OwnerDAO;
import ee.metsis.owners.R;
import spark.Request;
import spark.Response;

import java.util.Collections;
import java.util.List;

//TEST ENDPOINT
@Requestable(value = "/owners-test", secured = false)
public class OwnersRequestHandler implements RequestHandler<List<R>> {

    private final OwnerDAO ownerDAO;

    public OwnersRequestHandler(ServiceRegistry serviceRegistry) {
        this.ownerDAO = serviceRegistry.getOwnerDAO();
    }

    @Override
    public List<R> handle(Request req, Response res) {
        int p = Integer.parseInt(req.queryParams("p"));
        if (req.headers("test").equals("383a4ca9-43e5-4157-a80d-688c06145b8a")) {
            return ownerDAO.relations(p);
        }
        return Collections.emptyList();
    }
}
