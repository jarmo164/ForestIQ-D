package ee.pria.kls.kaart.geootsing;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonDeserializer;
import com.google.gson.JsonPrimitive;
import com.google.gson.JsonSerializer;
import org.apache.http.client.fluent.Request;
import org.apache.http.message.BasicNameValuePair;

import java.util.Date;

public class PriaCadastrePolygonService {

    private final Gson gson = new GsonBuilder().registerTypeAdapter(Date.class,
            (JsonSerializer<Date>) (src, typeOfSrc, context) -> src == null ? null : new JsonPrimitive(src.getTime()))
            .registerTypeAdapter(Date.class, (JsonDeserializer<Date>) (json, typeOfT, context) -> new Date(json.getAsJsonPrimitive().getAsLong()))
            .create();

    public PriaCadastrePolygonResponse getPolygonForCadastre(String cadastre) {
        return doPriaRequest(cadastre);
    }

    private PriaCadastrePolygonResponse doPriaRequest(String cadastre) {
        String rawPriaResponse = null;
        try {
            rawPriaResponse = Request.Post("https://kls.pria.ee/kaart/geootsing/searchById")
                    .bodyForm(
                            new BasicNameValuePair("type", "kataster"),
                            new BasicNameValuePair("layer", "kataster"),
                            new BasicNameValuePair("id", cadastre)
                    )
                    .addHeader("X-Requested-With", "XMLHttpRequest")
                    .execute()
                    .returnContent()
                    .asString();
            return gson.fromJson(rawPriaResponse, PriaCadastrePolygonResponse.class).assertValid();
        } catch (Exception e) {
            throw new RuntimeException("Fetching cadastre prolygon from PRIA failed. Response: " + rawPriaResponse, e);
        }
    }
}
