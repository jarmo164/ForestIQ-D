package ee.metsis.pria;

import ee.finenet.fineframe.geography.LatLng;

import java.util.List;
import java.util.Objects;

public class CadastrePolygon {
    private final List<List<LatLng>> coordinates;
    private final LatLng centroid;

    public CadastrePolygon(List<List<LatLng>> coordinates, LatLng centroid) {
        Objects.requireNonNull(coordinates, "PolygonData.coordinates can not be null");
        this.coordinates = coordinates;
        this.centroid = centroid;
    }

    public List<List<LatLng>> getCoordinates() {
        return coordinates;
    }

    public LatLng getCentroid() {
        return centroid;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;

        CadastrePolygon that = (CadastrePolygon) o;

        return coordinates.equals(that.coordinates);
    }

    @Override
    public int hashCode() {
        return coordinates.hashCode();
    }

    @Override
    public String toString() {
        return "PolygonData{" +
                ", coordinates=" + coordinates +
                '}';
    }
}
