package ee.metsis.pria;

import ee.metsis.coordinates.LEstGeoConverter;
import ee.pria.kls.kaart.geootsing.PriaCadastrePolygonService;

public class CadastrePolygonService {

    private final PriaCadastrePolygonService priaCadastrePolygonService;
    private final CadastrePolygonMapper mapper = new CadastrePolygonMapper(new LEstGeoConverter());

    public CadastrePolygonService(PriaCadastrePolygonService priaCadastrePolygonService) {
        this.priaCadastrePolygonService = priaCadastrePolygonService;
    }

    public CadastrePolygon getPolygonForCadastre(String cadastre) {
        return mapper.map(priaCadastrePolygonService.getPolygonForCadastre(cadastre));
    }
}
