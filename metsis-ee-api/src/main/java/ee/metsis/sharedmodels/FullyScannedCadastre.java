package ee.metsis.sharedmodels;

import ee.maaamet.geoportaal.xgis.GeoDetails;
import ee.metsad.register.models.CadastreSubSectionsDetails;
import ee.pria.kls.kaart.geootsing.PriaCadastrePolygonResponse;

public class FullyScannedCadastre {
    private String cadastre;
    private CadastreSubSectionsDetails forestSectionsDetails;
    private GeoDetails geoDetails;
    private PriaCadastrePolygonResponse cadastrePolygon;

    public String getCadastre() {
        return cadastre;
    }

    public void setCadastre(String cadastre) {
        this.cadastre = cadastre;
    }

    public CadastreSubSectionsDetails getForestSectionsDetails() {
        return forestSectionsDetails;
    }

    public void setForestSectionsDetails(CadastreSubSectionsDetails forestSectionsDetails) {
        this.forestSectionsDetails = forestSectionsDetails;
    }

    public GeoDetails getGeoDetails() {
        return geoDetails;
    }

    public void setGeoDetails(GeoDetails geoDetails) {
        this.geoDetails = geoDetails;
    }

    public PriaCadastrePolygonResponse getCadastrePolygon() {
        return cadastrePolygon;
    }

    public void setCadastrePolygon(PriaCadastrePolygonResponse cadastrePolygon) {
        this.cadastrePolygon = cadastrePolygon;
    }
}
