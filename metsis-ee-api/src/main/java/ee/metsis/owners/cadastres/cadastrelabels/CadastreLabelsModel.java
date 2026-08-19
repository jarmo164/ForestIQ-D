package ee.metsis.owners.cadastres.cadastrelabels;

import java.util.List;

public class CadastreLabelsModel {

    private List<CadastreLabel> setLabels;
    private List<CadastreLabel> notSetLabels;

    public List<CadastreLabel> getSetLabels() {
        return setLabels;
    }

    public void setSetLabels(List<CadastreLabel> setLabels) {
        this.setLabels = setLabels;
    }

    public List<CadastreLabel> getNotSetLabels() {
        return notSetLabels;
    }

    public void setNotSetLabels(List<CadastreLabel> notSetLabels) {
        this.notSetLabels = notSetLabels;
    }
}
