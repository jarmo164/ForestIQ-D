package ee.metsad.register.models;


import java.util.List;

public class CadastreSubsectionDetailsSubUnit {
    private String nimi;
    private List<CadastreSubsectionDetailsSection> eraldised;

    public List<CadastreSubsectionDetailsSection> getEraldised() {
        return eraldised;
    }

    public void setEraldised(List<CadastreSubsectionDetailsSection> eraldised) {
        this.eraldised = eraldised;
    }

    public String getNimi() {
        return nimi;
    }

    public void setNimi(String nimi) {
        this.nimi = nimi;
    }
}
