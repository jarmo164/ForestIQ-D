package ee.metsad.register.models;

public class ForestNotificationModel {
    private Long notificationId;
    private Long notificationNumber;
    private Long cadastreSubPartCode;
    private String workCode;
    private Long state;
    private String damageCode;
    private Double area;
    private Double amountToBeCut;
    private String decision;
    private Long registrationDate;
    private Long confirmationDate;
    private String cadastreNo;
    private Boolean archived;
    private Long archiveDate;

    public Long getNotificationId() {
        return notificationId;
    }

    public void setNotificationId(Long notificationId) {
        this.notificationId = notificationId;
    }

    public Long getNotificationNumber() {
        return notificationNumber;
    }

    public void setNotificationNumber(Long notificationNumber) {
        this.notificationNumber = notificationNumber;
    }

    public Long getCadastreSubPartCode() {
        return cadastreSubPartCode;
    }

    public void setCadastreSubPartCode(Long cadastreSubPartCode) {
        this.cadastreSubPartCode = cadastreSubPartCode;
    }

    public String getWorkCode() {
        return workCode;
    }

    public void setWorkCode(String workCode) {
        this.workCode = workCode;
    }

    public Long getState() {
        return state;
    }

    public void setState(Long state) {
        this.state = state;
    }

    public String getDamageCode() {
        return damageCode;
    }

    public void setDamageCode(String damageCode) {
        this.damageCode = damageCode;
    }

    public Double getArea() {
        return area;
    }

    public void setArea(Double area) {
        this.area = area;
    }

    public Double getAmountToBeCut() {
        return amountToBeCut;
    }

    public void setAmountToBeCut(Double amountToBeCut) {
        this.amountToBeCut = amountToBeCut;
    }

    public String getDecision() {
        return decision;
    }

    public void setDecision(String decision) {
        this.decision = decision;
    }

    public Long getRegistrationDate() {
        return registrationDate;
    }

    public void setRegistrationDate(Long registrationDate) {
        this.registrationDate = registrationDate;
    }

    public Long getConfirmationDate() {
        return confirmationDate;
    }

    public void setConfirmationDate(Long confirmationDate) {
        this.confirmationDate = confirmationDate;
    }

    public String getCadastreNo() {
        return cadastreNo;
    }

    public void setCadastreNo(String cadastreNo) {
        this.cadastreNo = cadastreNo;
    }

    public Boolean getArchived() {
        return archived;
    }

    public void setArchived(Boolean archived) {
        this.archived = archived;
    }

    public Long getArchiveDate() {
        return archiveDate;
    }

    public void setArchiveDate(Long archiveDate) {
        this.archiveDate = archiveDate;
    }

    @Override
    public String toString() {
        return "ForestNotificationModel{" +
                "notificationId=" + notificationId +
                ", notificationNumber=" + notificationNumber +
                ", cadastreSubPartCode=" + cadastreSubPartCode +
                ", workCode='" + workCode + '\'' +
                ", state=" + state +
                ", damageCode='" + damageCode + '\'' +
                ", area=" + area +
                ", amountToBeCut=" + amountToBeCut +
                ", decision='" + decision + '\'' +
                ", registrationDate=" + registrationDate +
                ", confirmationDate=" + confirmationDate +
                ", cadastreNo='" + cadastreNo + '\'' +
                ", archived=" + archived +
                ", archiveDate=" + archiveDate +
                '}';
    }
}
