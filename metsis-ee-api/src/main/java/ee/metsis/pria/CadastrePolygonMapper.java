package ee.metsis.pria;

import ee.finenet.fineframe.geography.LEstCoordinates;
import ee.finenet.fineframe.geography.LatLng;
import ee.metsis.coordinates.LEstGeoConverter;
import ee.pria.kls.kaart.geootsing.PriaCadastrePolygonFeature;
import ee.pria.kls.kaart.geootsing.PriaCadastrePolygonResponse;

import java.util.List;
import java.util.stream.Collectors;

public class CadastrePolygonMapper {

    private final LEstGeoConverter lEstGeoConverter;

    public CadastrePolygonMapper(LEstGeoConverter lEstGeoConverter) {
        this.lEstGeoConverter = lEstGeoConverter;
    }

    public CadastrePolygon map(PriaCadastrePolygonResponse serviceResponse) {
        PriaCadastrePolygonFeature feature = serviceResponse.getFeatures().get(0);
        List<List<LatLng>> coordinates = feature.getGeometry().getCoordinates().stream()
                .map(c -> c.stream().map(e -> lEstGeoConverter.lEstToGeo(new LEstCoordinates(e.get(1), e.get(0))))
                        .collect(Collectors.toList())).collect(Collectors.toList());
        List<Double> centr = feature.getProperties().getCentroid();
        LatLng centroid = lEstGeoConverter.lEstToGeo(new LEstCoordinates(centr.get(1), centr.get(0)));
        return new CadastrePolygon(coordinates, centroid);
    }
}
