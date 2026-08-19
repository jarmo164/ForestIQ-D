package ee.metsis.owners.cadastres.cadastrelabels;

import ee.finenet.fineframe.geography.LatLng;

import java.util.List;

public class ForestPlanCadastreSubPart {
    private Integer subPartCode;
    private String treeTypeCode;
    private Double area;
    private List<List<LatLng>> polygon;

    public Integer getSubPartCode() {
        return subPartCode;
    }

    public void setSubPartCode(Integer subPartCode) {
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

    public List<List<LatLng>> getPolygon() {
        return polygon;
    }

    public void setPolygon(List<List<LatLng>> polygon) {
        this.polygon = polygon;
    }
}
