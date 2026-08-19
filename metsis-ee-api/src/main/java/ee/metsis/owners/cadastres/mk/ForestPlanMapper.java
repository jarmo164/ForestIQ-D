package ee.metsis.owners.cadastres.mk;

import com.google.gson.Gson;
import ee.finenet.fineframe.geography.LEstCoordinates;
import ee.finenet.fineframe.geography.LatLng;
import ee.metsad.register.models.CadastreSubSectionsDetails;
import ee.metsad.register.models.CadastreSubSectionCoodrinates;
import ee.metsis.coordinates.LEstGeoConverter;
import ee.metsis.owners.cadastres.cadastrelabels.ForestPlanCadastreSubPart;

import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

public class ForestPlanMapper {

    public ForestPlan map(CadastreSubSectionsDetails serviceResponse, String cadastre) {
        LEstGeoConverter lEstGeoConverter = new LEstGeoConverter();
        Gson gson = new Gson();
        List<ForestPlanCadastreSubPart> result = new ArrayList<>();
        ForestPlan forestPlan = new ForestPlan();
        serviceResponse.getAlamYksused().stream().filter(ay -> cadastre.equals(ay.getNimi())).flatMap(metsAveEraldisAlamYksus -> metsAveEraldisAlamYksus.getEraldised().stream())
                .forEach(eraldis -> {
                    forestPlan.setRegistrationDate(eraldis.getRegKp());
                    CadastreSubSectionCoodrinates geoJson = gson.fromJson(eraldis.getAlaGeoJson(), CadastreSubSectionCoodrinates.class);
                    List<List<LatLng>> coords = geoJson.getCoordinates().get(0).stream()
                            .map(ld ->
                                    ld.stream().map(ldd ->
                                            lEstGeoConverter.lEstToGeo(new LEstCoordinates(ldd.get(1), ldd.get(0)))
                                    ).collect(Collectors.toList())
                            ).collect(Collectors.toList());
                    ForestPlanCadastreSubPart e = new ForestPlanCadastreSubPart();
                    e.setSubPartCode(eraldis.getEraldiseNr());
                    e.setPolygon(coords);
                    e.setArea(eraldis.getPindala());
                    e.setTreeTypeCode(eraldis.getPeapuuliik());
                    result.add(e);
                });
        forestPlan.setCadastreNo(cadastre);
        forestPlan.setCadastreSubParts(result);
        return forestPlan;
    }
}
