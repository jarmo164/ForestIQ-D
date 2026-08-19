package ee.finenet.fineframe.geography;

import com.google.gson.reflect.TypeToken;

import java.lang.reflect.Type;
import java.util.List;

public class LatLng {

    public static final Type GSON_POLYGON_TYPE = new TypeToken<List<List<ee.finenet.fineframe.geography.LatLng>>>() {
    }.getType();

    private double lat;
    private double lng;

    public LatLng() {

    }

    public LatLng(double lat, double lng) {
        this.lat = lat;
        this.lng = lng;
    }

    public double getLat() {
        return lat;
    }

    public double getLng() {
        return lng;
    }

    public void setLat(double lat) {
        this.lat = lat;
    }

    public void setLng(double lng) {
        this.lng = lng;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;

        ee.finenet.fineframe.geography.LatLng latLng = (ee.finenet.fineframe.geography.LatLng) o;

        return Double.compare(latLng.lat, lat) == 0 && Double.compare(latLng.lng, lng) == 0;
    }

    @Override
    public int hashCode() {
        int result;
        long temp;
        temp = Double.doubleToLongBits(lat);
        result = (int) (temp ^ (temp >>> 32));
        temp = Double.doubleToLongBits(lng);
        result = 31 * result + (int) (temp ^ (temp >>> 32));
        return result;
    }

    @Override
    public String toString() {
        return "LatLng{" +
                "lat=" + lat +
                ", lng=" + lng +
                '}';
    }
}
