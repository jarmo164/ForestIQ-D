package ee.metsad.register.models;

public class CadastreSubsectionDetailsSection {
    private Integer id;
    private Integer eraldiseNr;
    private String alaGeoJson;
    private String peapuuliik;
    private Double pindala;
    private Long regKp;

    public Integer getId() {
        return id;
    }

    public void setId(Integer id) {
        this.id = id;
    }

    public Integer getEraldiseNr() {
        return eraldiseNr;
    }

    public void setEraldiseNr(Integer eraldiseNr) {
        this.eraldiseNr = eraldiseNr;
    }

    public String getAlaGeoJson() {
        return alaGeoJson;
    }

    public void setAlaGeoJson(String alaGeoJson) {
        this.alaGeoJson = alaGeoJson;
    }

    public String getPeapuuliik() {
        return peapuuliik;
    }

    public void setPeapuuliik(String peapuuliik) {
        this.peapuuliik = peapuuliik;
    }

    public Long getRegKp() {
        return regKp;
    }

    public void setRegKp(Long regKp) {
        this.regKp = regKp;
    }

    public Double getPindala() {
        return pindala;
    }

    public void setPindala(Double pindala) {
        this.pindala = pindala;
    }
}
