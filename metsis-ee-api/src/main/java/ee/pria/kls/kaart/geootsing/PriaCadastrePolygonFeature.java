package ee.pria.kls.kaart.geootsing;

public class PriaCadastrePolygonFeature {

    private String type;
    private PriaCadastrePolygonProperties properties;
    private PriaCadastrePolygonGeometry geometry;

    public String getType() {
        return type;
    }

    public void setType(String type) {
        this.type = type;
    }

    public PriaCadastrePolygonProperties getProperties() {
        return properties;
    }

    public void setProperties(PriaCadastrePolygonProperties properties) {
        this.properties = properties;
    }

    public PriaCadastrePolygonGeometry getGeometry() {
        return geometry;
    }

    public void setGeometry(PriaCadastrePolygonGeometry geometry) {
        this.geometry = geometry;
    }
}
