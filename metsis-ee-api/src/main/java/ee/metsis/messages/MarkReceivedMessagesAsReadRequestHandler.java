package ee.metsis.messages;

import ee.finenet.fineframe.http.AbstractRequestHandler;
import ee.finenet.fineframe.http.RequestMethod;
import ee.finenet.fineframe.http.Requestable;
import ee.finenet.fineframe.http.genericmodels.OkResponse;
import ee.finenet.fineframe.serialization.GsonHolder;
import ee.metsis.ServiceRegistry;
import ee.metsis.security.LimitedPrivilegesChecks;
import spark.Request;
import spark.Response;

import java.util.Collection;
import java.util.Date;

@Requestable(value = "/messages/received/mark-as-read", method = RequestMethod.POST)
public class MarkReceivedMessagesAsReadRequestHandler extends AbstractRequestHandler {

    private final MessagesService messagesService;

    public MarkReceivedMessagesAsReadRequestHandler(ServiceRegistry serviceRegistry) {
        this.messagesService = serviceRegistry.getMessagesService();
    }

    @Override
    protected OkResponse handleRequest(Request req, Response res) {
        MarkReadUntil inp = GsonHolder.GSON.fromJson(req.body(), MarkReadUntil.class);
        Date until = inp.getMarkReadUntil();
        messagesService.markMessagesUpToSpecifiedDateNoticed(until, LimitedPrivilegesChecks.getLoggedInUser(req));
        return OkResponse.INSTANCE;
    }

    @Override
    protected Collection<String> requireAtLeastOneOfPrivileges() {
        return noPrivilegesRequired();
    }
}
