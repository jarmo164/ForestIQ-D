package ee.pria.kls.kaart.geootsing;

import java.util.List;

public class PriaCadastrePolygonProperties {

    private String fid;
    private String layer;
    private String symbol;
    private List<Double> centroid;
    private String popup;

    public String getFid() {
        return fid;
    }

    public void setFid(String fid) {
        this.fid = fid;
    }

    public String getLayer() {
        return layer;
    }

    public void setLayer(String layer) {
        this.layer = layer;
    }

    public String getSymbol() {
        return symbol;
    }

    public void setSymbol(String symbol) {
        this.symbol = symbol;
    }

    public List<Double> getCentroid() {
        return centroid;
    }

    public void setCentroid(List<Double> centroid) {
        this.centroid = centroid;
    }

    public String getPopup() {
        return popup;
    }

    public void setPopup(String popup) {
        this.popup = popup;
    }
}
