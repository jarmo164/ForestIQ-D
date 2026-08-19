package ee.metsis.personsdump;

import ee.finenet.fineframe.http.AbstractRequestHandler;
import ee.finenet.fineframe.http.Requestable;
import ee.metsis.ServiceRegistry;
import ee.metsis.security.Privilege;
import spark.Request;
import spark.Response;

import java.util.Collection;

@Requestable("/persons-dump")
public class SearchPersonsDumpRequestHandler extends AbstractRequestHandler {

    private final PersonsDumpService personsDumpService;

    public SearchPersonsDumpRequestHandler(ServiceRegistry serviceRegistry) {
        this.personsDumpService = serviceRegistry.getPersonsDumpService();
    }

    @Override
    protected Object handleRequest(Request req, Response res) {
        return personsDumpService.searchEntries(new PersonsDumpCriteria(req));
    }

    @Override
    protected Collection<String> requireAtLeastOneOfPrivileges() {
        return privileges(Privilege.PHONES.name());
    }
}
