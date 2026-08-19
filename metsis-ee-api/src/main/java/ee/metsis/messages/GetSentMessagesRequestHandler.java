package ee.metsis.messages;

import ee.finenet.fineframe.http.AbstractRequestHandler;
import ee.finenet.fineframe.http.Requestable;
import ee.metsis.ServiceRegistry;
import ee.metsis.security.LimitedPrivilegesChecks;
import spark.Request;
import spark.Response;

import java.util.Collection;
import java.util.List;

@Requestable("/messages/sent")
public class GetSentMessagesRequestHandler extends AbstractRequestHandler {

    private final MessagesService messagesService;

    public GetSentMessagesRequestHandler(ServiceRegistry serviceRegistry) {
        this.messagesService = serviceRegistry.getMessagesService();
    }

    @Override
    protected List<Message> handleRequest(Request req, Response res) {
        int page = Integer.parseInt(req.queryParams("page"));
        int size = Integer.parseInt(req.queryParams("size"));
        return messagesService.getPageOfNewestSentMessages(LimitedPrivilegesChecks.getLoggedInUser(req), size, page);
    }

    @Override
    protected Collection<String> requireAtLeastOneOfPrivileges() {
        return noPrivilegesRequired();
    }
}
