package ee.metsad.register.services;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonDeserializer;
import com.google.gson.JsonPrimitive;
import com.google.gson.JsonSerializer;
import com.google.gson.reflect.TypeToken;
import ee.metsad.register.internalmodels.forestnotification.MetsAveTeatisAlamYksus;
import ee.metsad.register.internalmodels.forestnotification.MetsAveTeatisDetailsResponse;
import ee.metsad.register.internalmodels.forestnotification.MetsAveTeatisRespPart;
import ee.metsad.register.internalmodels.forestnotification.MetsAveTeatisTeatis;
import ee.metsad.register.models.CadastreSubSectionsDetails;
import ee.metsad.register.mappers.ForestNotificationsResponseMapper;
import ee.metsad.register.models.ForestNotificationModel;
import org.apache.http.client.fluent.Request;

import java.io.IOException;
import java.lang.reflect.Type;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

public class ForestRegistryService {

    private final static  Type LIST_OF_METS_AVE_TEATIS_TYPE = new TypeToken<ArrayList<MetsAveTeatisRespPart>>() {
    }.getType();
    private final static String TEATISED_DETAILS_URL_TEMPLATE = "https://register.metsad.ee/api/rest/teatis/teatisVaatamine/%s";
    private final static String TEATISED_URL_TEMPLATE = "https://register.metsad.ee/api/rest/teatis/puu?katastriNr=%s&naitaAegunud=true";
    private final static String MK_BY_KATASTER_URL_TEMPLATE = "https://register.metsad.ee/api/rest/eraldis/puu?katastriNr=%s";

    private final Gson gson = new GsonBuilder().registerTypeAdapter(Date.class,
            (JsonSerializer<Date>) (src, typeOfSrc, context) -> src == null ? null : new JsonPrimitive(src.getTime()))
            .registerTypeAdapter(Date.class, (JsonDeserializer<Date>) (json, typeOfT, context) -> new Date(json.getAsJsonPrimitive().getAsLong()))
            .create();

    private final ForestNotificationsResponseMapper forestNotificationsResponseMapper = new ForestNotificationsResponseMapper();

    public ForestNotificationModel getNotificationById(Long id) {
        return forestNotificationsResponseMapper.map(executeMRTeatisDetailsService(id));
    }

    public List<ForestNotificationModel> getNotificationsForCadastre(String cadastre) {
        List<MetsAveTeatisAlamYksus> alamYksused = executeMRTeatisService(cadastre);

        return collectTeatised(alamYksused).parallelStream().map(metsAveTeatis -> {
            Long teatisId = metsAveTeatis.getTeatisId();
            MetsAveTeatisDetailsResponse teatisResp = executeMRTeatisDetailsService(teatisId);
            return forestNotificationsResponseMapper.map(teatisResp);
        }).sorted((o1, o2) -> o2.getRegistrationDate().compareTo(o1.getRegistrationDate())).collect(Collectors.toList());
    }

    public Optional<CadastreSubSectionsDetails> getCadastrePolygonDetails(String cadastre) {
        try {
            String json = doHttpGet(String.format(MK_BY_KATASTER_URL_TEMPLATE,
                    cadastre));
            List<CadastreSubSectionsDetails> mrPolygonRespParts = gson.fromJson(json, new TypeToken<ArrayList<CadastreSubSectionsDetails>>() {
            }.getType());
            if (!mrPolygonRespParts.isEmpty()) {
                return Optional.of(mrPolygonRespParts.get(0));
            }
        } catch (Exception e) {
            throw new RuntimeException(String.format("Failed to query metsaregister for cadastre %s", cadastre), e);
        }
        return Optional.empty();
    }

    private MetsAveTeatisDetailsResponse executeMRTeatisDetailsService(Long teatisId) {
        try {
            return gson.fromJson(doHttpGet(String.format(TEATISED_DETAILS_URL_TEMPLATE, teatisId)),
                    MetsAveTeatisDetailsResponse.class);
        } catch (Exception e) {
            throw new RuntimeException(String.format("Failed to query notification with id %s", teatisId), e);
        }
    }

    private List<MetsAveTeatisAlamYksus> executeMRTeatisService(String cadastre) {
        try {
            List<MetsAveTeatisRespPart> teatidRespParts = gson.fromJson(
                    doHttpGet(String.format(TEATISED_URL_TEMPLATE, cadastre)), LIST_OF_METS_AVE_TEATIS_TYPE);
            return teatidRespParts.stream().flatMap(m -> m.getAlamYksused().stream()).collect(Collectors.toList());
        } catch (Exception e) {
            throw new RuntimeException(String.format("Failed to query forest registry for cadastre %s", cadastre), e);
        }
    }

    private String doHttpGet(String url) throws IOException {
        return Request.Get(url).execute().returnContent().asString();
    }

    private List<MetsAveTeatisTeatis> collectTeatised(List<MetsAveTeatisAlamYksus> alamYksused) {
        return alamYksused.stream().map(MetsAveTeatisAlamYksus::getTeatised).flatMap(List::stream).collect(Collectors.toList());
    }
}
