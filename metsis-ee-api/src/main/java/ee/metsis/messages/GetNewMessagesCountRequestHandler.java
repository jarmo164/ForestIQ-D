package ee.metsis.messages;

import ee.finenet.fineframe.http.AbstractRequestHandler;
import ee.finenet.fineframe.http.Requestable;
import ee.metsis.ServiceRegistry;
import ee.metsis.security.LimitedPrivilegesChecks;
import spark.Request;
import spark.Response;

import java.util.Collection;

@Requestable("/messages/new/count")
public class GetNewMessagesCountRequestHandler extends AbstractRequestHandler {

    private final MessagesService messagesService;

    public GetNewMessagesCountRequestHandler(ServiceRegistry serviceRegistry) {
        this.messagesService = serviceRegistry.getMessagesService();
    }

    @Override
    protected NewMessagesCount handleRequest(Request req, Response res) {
        return new NewMessagesCount(messagesService.getNumberOfUnnoticedMessages(LimitedPrivilegesChecks.getLoggedInUser(req)));
    }

    @Override
    protected Collection<String> requireAtLeastOneOfPrivileges() {
        return noPrivilegesRequired();
    }
}
