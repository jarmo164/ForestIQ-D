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

@Requestable(value = "/messages/send", method = RequestMethod.POST)
public class SendDirectMessageRequestHandler extends AbstractRequestHandler {

    private final MessagesService messagesService;

    public SendDirectMessageRequestHandler(ServiceRegistry serviceRegistry) {
        this.messagesService = serviceRegistry.getMessagesService();
    }

    @Override
    protected OkResponse handleRequest(Request req, Response res) {
        String body = req.body();
        NewDirectMessage message = GsonHolder.GSON.fromJson(body, NewDirectMessage.class);
        if (message == null ||
                message.getMessage() == null ||
                message.getRecipients() == null ||
                message.getRecipients().isEmpty()) {
            throw new IllegalArgumentException("Direct message was invalid: " + body);
        }
        String sender = LimitedPrivilegesChecks.getLoggedInUser(req);
        message.getRecipients().stream().distinct().forEach(recipient -> messagesService.sendMessage(message.getMessage(), sender, recipient));
        return OkResponse.INSTANCE;
    }

    @Override
    protected Collection<String> requireAtLeastOneOfPrivileges() {
        return noPrivilegesRequired();
    }
}
