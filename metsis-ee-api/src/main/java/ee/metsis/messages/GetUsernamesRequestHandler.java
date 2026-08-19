package ee.metsis.messages;

import ee.finenet.fineframe.http.AbstractRequestHandler;
import ee.finenet.fineframe.http.Requestable;
import ee.metsis.ServiceRegistry;
import spark.Request;
import spark.Response;

import java.util.Collection;
import java.util.List;

@Requestable("/messages/usernames")
public class GetUsernamesRequestHandler extends AbstractRequestHandler {

    private final MessagesService messagesService;

    public GetUsernamesRequestHandler(ServiceRegistry serviceRegistry) {
        this.messagesService = serviceRegistry.getMessagesService();
    }

    @Override
    protected List<String> handleRequest(Request req, Response res) {
        return messagesService.getUsernames();
    }

    @Override
    protected Collection<String> requireAtLeastOneOfPrivileges() {
        return noPrivilegesRequired();
    }
}
