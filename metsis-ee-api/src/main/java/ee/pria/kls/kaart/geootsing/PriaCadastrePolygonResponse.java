package ee.pria.kls.kaart.geootsing;

import java.util.List;
import java.util.Objects;

public class PriaCadastrePolygonResponse {

    private String type;
    private List<PriaCadastrePolygonFeature> features;

    public PriaCadastrePolygonResponse assertValid() {
        PriaCadastrePolygonFeature feature = getFeatures().get(0);
        try {
            Objects.requireNonNull(feature.getGeometry().getCoordinates().get(0).get(0));
            Objects.requireNonNull(feature.getProperties().getCentroid().get(0));
            return this;
        } catch (Exception e) {
            throw new RuntimeException("PriaCadastrePolygonResponse does not contain enough information to be considered valid");
        }
    }

    public String getType() {
        return type;
    }

    public void setType(String type) {
        this.type = type;
    }

    public List<PriaCadastrePolygonFeature> getFeatures() {
        return features;
    }

    public void setFeatures(List<PriaCadastrePolygonFeature> features) {
        this.features = features;
    }

}
