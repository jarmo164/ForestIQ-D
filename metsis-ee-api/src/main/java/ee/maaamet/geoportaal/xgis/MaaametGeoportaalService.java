package ee.maaamet.geoportaal.xgis;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonDeserializer;
import com.google.gson.JsonPrimitive;
import com.google.gson.JsonSerializer;
import org.apache.http.client.fluent.Request;

import java.io.IOException;
import java.util.Date;
import java.util.Map;

public class MaaametGeoportaalService {

    private static final String DETAILED_INFO_REQ_TEMPLATE = "http://geoportaal.maaamet.ee/url/xgis-ky.php?ky=%s&out=json";

    private final Gson gson = new GsonBuilder().registerTypeAdapter(Date.class,
            (JsonSerializer<Date>) (src, typeOfSrc, context) -> src == null ? null : new JsonPrimitive(src.getTime()))
            .registerTypeAdapter(Date.class, (JsonDeserializer<Date>) (json, typeOfT, context) -> new Date(json.getAsJsonPrimitive().getAsLong()))
            .create();

    private final GeoDetailsMapper mapper = new GeoDetailsMapper();

    public GeoDetails getDetailedInfo(String cadastre) {
        String url = String.format(DETAILED_INFO_REQ_TEMPLATE, cadastre);
        return mapper.map(extractResponseInternals(
                parseResponseJson(
                        doGetRequest(url),
                        url
                ), url));
    }

    private String doGetRequest(String url) {
        try {
            return Request.Get(url).execute().returnContent().asString();
        } catch (IOException e) {
            throw new RuntimeException(String.format("Fetching polygon from URL %s failed", url));
        }
    }

    private Map parseResponseJson(String httpResponse, String url) {
        try {
            return gson.fromJson(httpResponse, Map.class);
        } catch (Exception e) {
            throw new RuntimeException(String.format("Was not able to parse service response of URL '%s'. " +
                    "Response contents: '%s'.", url, httpResponse), e);
        }
    }

    @SuppressWarnings("unchecked")
    private Map<String, String> extractResponseInternals(Map<?, ?> response, String url) {
        if (response.isEmpty() || !response.containsKey("1")) {
            throw new RuntimeException(String.format("%s responded with something unexpected: %s", url, response));
        }

        Object internals = response.get("1");
        if (internals instanceof Map) {
            return (Map) internals;
        } else {
            throw new RuntimeException(String.format("%s responded with something unexpected: %s", url, response));
        }
    }
}
