package ee.metsis.owners.cadastres.registryfeatures;

public class ForestRegistryFeature {
    private Long id;
    private String sourceLayer;
    private String sourceId;
    private String cadastreId;
    private Integer subpartCode;
    private String title;
    private String workCode;
    private String decision;
    private Double area;
    private Double volume;
    private Long eventDate;
    private String attributes;
    private String geometry;

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getSourceLayer() {
        return sourceLayer;
    }

    public void setSourceLayer(String sourceLayer) {
        this.sourceLayer = sourceLayer;
    }

    public String getSourceId() {
        return sourceId;
    }

    public void setSourceId(String sourceId) {
        this.sourceId = sourceId;
    }

    public String getCadastreId() {
        return cadastreId;
    }

    public void setCadastreId(String cadastreId) {
        this.cadastreId = cadastreId;
    }

    public Integer getSubpartCode() {
        return subpartCode;
    }

    public void setSubpartCode(Integer subpartCode) {
        this.subpartCode = subpartCode;
    }

    public String getTitle() {
        return title;
    }

    public void setTitle(String title) {
        this.title = title;
    }

    public String getWorkCode() {
        return workCode;
    }

    public void setWorkCode(String workCode) {
        this.workCode = workCode;
    }

    public String getDecision() {
        return decision;
    }

    public void setDecision(String decision) {
        this.decision = decision;
    }

    public Double getArea() {
        return area;
    }

    public void setArea(Double area) {
        this.area = area;
    }

    public Double getVolume() {
        return volume;
    }

    public void setVolume(Double volume) {
        this.volume = volume;
    }

    public Long getEventDate() {
        return eventDate;
    }

    public void setEventDate(Long eventDate) {
        this.eventDate = eventDate;
    }

    public String getAttributes() {
        return attributes;
    }

    public void setAttributes(String attributes) {
        this.attributes = attributes;
    }

    public String getGeometry() {
        return geometry;
    }

    public void setGeometry(String geometry) {
        this.geometry = geometry;
    }
}
