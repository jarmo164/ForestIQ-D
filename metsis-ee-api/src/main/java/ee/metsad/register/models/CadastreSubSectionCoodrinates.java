package ee.metsad.register.models;

import java.util.List;

public class CadastreSubSectionCoodrinates {
    private List<List<List<List<Double>>>> coordinates;

    public List<List<List<List<Double>>>> getCoordinates() {
        return coordinates;
    }

    public void setCoordinates(List<List<List<List<Double>>>> coordinates) {
        this.coordinates = coordinates;
    }
}
