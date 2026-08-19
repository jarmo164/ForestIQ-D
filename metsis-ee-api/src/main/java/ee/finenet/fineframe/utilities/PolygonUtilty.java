package ee.finenet.fineframe.utilities;

import com.google.gson.Gson;
import com.google.gson.reflect.TypeToken;
import ee.finenet.fineframe.geography.LEstCoordinates;
import ee.finenet.fineframe.geography.LatLng;
import ee.metsis.coordinates.LEstGeoConverter;

import java.lang.reflect.Type;
import java.util.ArrayList;
import java.util.List;

public class PolygonUtilty {
    private static final Type POLY_TYPE = new TypeToken<List<List<LatLng>>>() {
    }.getType();
    private static Gson gson = new Gson();
    private static final LEstGeoConverter lEstGeoConverter = new LEstGeoConverter();

    public static List<List<LatLng>> deserializePolygon(String inp) {
        if (inp == null || inp.trim().isEmpty()) {
            return null;
        }
        String trimmed = inp.trim();
        if (trimmed.startsWith("POLYGON") || trimmed.startsWith("MULTIPOLYGON")) {
            return deserializeWktPolygon(trimmed);
        }
        return gson.fromJson(inp, POLY_TYPE);
    }

    public static LatLng deserializeCentroid(String inp) {
        return gson.fromJson(inp, LatLng.class);
    }

    public static String serializePolygon(List<List<LatLng>> inp) {
        return gson.toJson(inp);
    }

    public static String serializeCentroid(LatLng inp) {
        if (inp == null) {
            return "{}";
        }
        return gson.toJson(inp);
    }

    public static LatLng approximateCentroid(List<List<LatLng>> polygon) {
        if (polygon == null || polygon.isEmpty() || polygon.get(0).isEmpty()) {
            return null;
        }
        double latSum = 0.0;
        double lngSum = 0.0;
        int count = 0;
        for (LatLng point : polygon.get(0)) {
            latSum += point.getLat();
            lngSum += point.getLng();
            count++;
        }
        return new LatLng(latSum / count, lngSum / count);
    }

    private static List<List<LatLng>> deserializeWktPolygon(String wkt) {
        List<List<LatLng>> rings = new ArrayList<>();
        int ringDepth = wkt.startsWith("MULTIPOLYGON") ? 3 : 2;
        int depth = 0;
        StringBuilder ring = null;
        for (int i = 0; i < wkt.length(); i++) {
            char c = wkt.charAt(i);
            if (c == '(') {
                depth++;
                if (depth == ringDepth) {
                    ring = new StringBuilder();
                }
                continue;
            }
            if (c == ')') {
                if (depth == ringDepth && ring != null) {
                    rings.add(parseWktRing(ring.toString()));
                    ring = null;
                }
                depth--;
                continue;
            }
            if (depth == ringDepth && ring != null) {
                ring.append(c);
            }
        }
        return rings;
    }

    private static List<LatLng> parseWktRing(String ring) {
        List<LatLng> result = new ArrayList<>();
        for (String coordinatePair : ring.split(",")) {
            String[] ordinates = coordinatePair.trim().split("\\s+");
            if (ordinates.length < 2) {
                continue;
            }
            double x = Double.parseDouble(ordinates[0]);
            double y = Double.parseDouble(ordinates[1]);
            result.add(lEstGeoConverter.lEstToGeo(new LEstCoordinates(x, y)));
        }
        return result;
    }
}
