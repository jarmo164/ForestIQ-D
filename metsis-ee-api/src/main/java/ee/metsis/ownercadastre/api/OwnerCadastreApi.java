package ee.metsis.ownercadastre.api;

import com.google.gson.Gson;
import com.google.gson.stream.JsonReader;
import com.google.gson.stream.JsonToken;
import org.apache.http.HttpResponse;
import org.apache.http.client.fluent.Request;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Function;
import java.util.stream.Collectors;

public class OwnerCadastreApi {
    private final String endpoint;
    private final String token;

    private final Gson gson = new Gson();
    private static final String AUTH_HEADER = "Authorization";
    private static final String OWNER_TYPE_PARAM = "ownerType";
    private static final String SINCE_PARAM = "since";
    private static final String SKIP_PARAM = "skip";
    private static final String LIMIT_PARAM = "limit";
    private static final DateTimeFormatter DATE_FORMAT = DateTimeFormatter.ofPattern("dd-MM-yyyy");
    private static final Logger logger = LoggerFactory.getLogger(OwnerCadastreApi.class);

    public OwnerCadastreApi(String endpoint, String token) {
        this.endpoint = endpoint;
        this.token = token;
    }

    public void downloadOwnersAndExecuteOnEachOwner(
            int skip,
            int limit,
            LocalDate since,
            Function<ExternalOwnerApiResponseRow, Void> action
    ) {
        if (!isEnabled()) {
            logger.warn("Owner Cadastre API is not enabled!");
        }
        String url = endpoint +
                "?" + OWNER_TYPE_PARAM + "=COMPANY" +
                "&" + OWNER_TYPE_PARAM + "=PERSON" +
                "&" + SKIP_PARAM + "=" + skip +
                "&" + LIMIT_PARAM + "=" + limit;
        if (since != null) {
            url += ("&" + SINCE_PARAM + "=" + DATE_FORMAT.format(since));
        }

        try (InputStream is = performRequest(url)) {
            processResponseStream(is, action);
        } catch (Exception e) {
            throw new RuntimeException("Simo API request failed", e);
        }
    }

    public boolean isEnabled() {
        return endpoint != null;
    }

    private void processResponseStream(InputStream is, Function<ExternalOwnerApiResponseRow, Void> action) throws IOException {
        JsonReader reader = new JsonReader(new InputStreamReader(is, StandardCharsets.UTF_8));
        if (reader.peek() != JsonToken.BEGIN_ARRAY) {
            throw new IllegalStateException("Unexpected response");
        }
        reader.beginArray();

        while (reader.hasNext()) {
            ExternalOwnerApiResponseRow row = gson.fromJson(reader, ExternalOwnerApiResponseRow.class);
            action.apply(row);
        }

        reader.endArray();
        reader.close();
    }

    private InputStream performRequest(String url) throws IOException {
        Request req = Request.Get(url);
        req.addHeader(AUTH_HEADER, token);
        logger.info("Requesting URL " + url);
        HttpResponse response = req.execute().returnResponse();
        int statusCode = response.getStatusLine().getStatusCode();
        if (statusCode / 100 != 2) {
            AtomicInteger linesRead = new AtomicInteger(0);
            String responseBody = new BufferedReader(new InputStreamReader(response.getEntity().getContent()))
                    .lines()
                    .takeWhile((x) -> linesRead.incrementAndGet() < 20)
                    .collect(Collectors.joining("\n"));
            throw new IllegalStateException("Unexpexted response status " + statusCode + ". Response body:\n" + responseBody);
        }
        return response.getEntity().getContent();
    }
}
