package ee.metsis.owners.cadastres;

import ee.finenet.fineframe.geography.LatLng;

import java.util.List;

public class CadastreMinimal {
    private String id;
    private String name;
    private LatLng centroid;
    private List<List<LatLng>> polygon;
    private Double area;
    private Boolean marked;
    private String type;

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public ee.finenet.fineframe.geography.LatLng getCentroid() {
        return centroid;
    }

    public void setCentroid(ee.finenet.fineframe.geography.LatLng centroid) {
        this.centroid = centroid;
    }

    public List<List<LatLng>> getPolygon() {
        return polygon;
    }

    public void setPolygon(List<List<LatLng>> polygon) {
        this.polygon = polygon;
    }

    public Double getArea() {
        return area;
    }

    public void setArea(Double area) {
        this.area = area;
    }

    public Boolean getMarked() {
        return marked;
    }

    public void setMarked(Boolean marked) {
        this.marked = marked;
    }

    public String getType() {
        return type;
    }

    public void setType(String type) {
        this.type = type;
    }
}
