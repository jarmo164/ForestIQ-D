package ee.metsis.personsdump;

import ee.finenet.fineframe.http.AbstractRequestHandler;
import ee.finenet.fineframe.http.RequestMethod;
import ee.finenet.fineframe.http.Requestable;
import ee.finenet.fineframe.http.genericmodels.OkResponse;
import ee.finenet.fineframe.serialization.GsonHolder;
import ee.metsis.ServiceRegistry;
import ee.metsis.security.Privilege;
import spark.Request;
import spark.Response;

import java.util.Collection;

@Requestable(value = "/persons-dump", method = RequestMethod.POST)
public class AddEntryToPersonsDumpRequestHandler extends AbstractRequestHandler {

    private final PersonsDumpService personsDumpService;

    public AddEntryToPersonsDumpRequestHandler(ServiceRegistry serviceRegistry) {
        this.personsDumpService = serviceRegistry.getPersonsDumpService();
    }

    @Override
    protected Object handleRequest(Request req, Response res) {
        NewPersonsDumpEntry entry = GsonHolder.GSON.fromJson(req.body(), NewPersonsDumpEntry.class);
        personsDumpService.addEntry(entry);
        return OkResponse.INSTANCE;
    }

    @Override
    protected Collection<String> requireAtLeastOneOfPrivileges() {
        return privileges(Privilege.PHONES.name());
    }
}
