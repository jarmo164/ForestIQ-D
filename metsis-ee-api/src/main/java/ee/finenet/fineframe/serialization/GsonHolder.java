package ee.finenet.fineframe.serialization;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonDeserializer;
import com.google.gson.JsonPrimitive;
import com.google.gson.JsonSerializer;
import ee.finenet.fineframe.utilities.DateUtility;

import java.util.Date;

public class GsonHolder {

    public static final Gson GSON = new GsonBuilder().registerTypeAdapter(Date.class,
            (JsonSerializer<Date>) (src, typeOfSrc, context) -> src == null ? null : new JsonPrimitive(src.getTime()))
            .registerTypeAdapter(Date.class, (JsonDeserializer<Date>) (json, typeOfT, context) -> {
                try {
                    return new Date(json.getAsJsonPrimitive().getAsLong());
                } catch (Exception e) {
                    String asString = json.getAsJsonPrimitive().getAsString();
                    return DateUtility.parseUTCISO8601(asString);
                }
            })
            .create();

}
