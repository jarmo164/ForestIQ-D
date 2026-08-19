package ee.metsis.owners.cadastres.mk;

import ee.finenet.fineframe.geography.LatLng;

import java.util.List;

public class CadastreSubPartData {
    private String subPartCode;
    private String treeTypeCode;
    private Double area;
    private List<LatLng> polygon;

    public String getSubPartCode() {
        return subPartCode;
    }

    public void setSubPartCode(String subPartCode) {
        this.subPartCode = subPartCode;
    }

    public String getTreeTypeCode() {
        return treeTypeCode;
    }

    public void setTreeTypeCode(String treeTypeCode) {
        this.treeTypeCode = treeTypeCode;
    }

    public Double getArea() {
        return area;
    }

    public void setArea(Double area) {
        this.area = area;
    }

    public List<LatLng> getPolygon() {
        return polygon;
    }

    public void setPolygon(List<LatLng> polygon) {
        this.polygon = polygon;
    }
}
