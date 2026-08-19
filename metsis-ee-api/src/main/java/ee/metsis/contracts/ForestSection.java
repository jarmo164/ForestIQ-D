package ee.metsis.contracts;

import java.text.DecimalFormat;

public class ForestSection {

    private static final DecimalFormat DECIMAT_FORMAT_1_AFTER_COMMA = new DecimalFormat("0.0");

    private Integer sectionNumber;
    private Double area;
    private Double amountToBeCut;
    private String typeOfWork;
    private String notificationId;

    public Integer getSectionNumber() {
        return sectionNumber;
    }

    public void setSectionNumber(Integer sectionNumber) {
        this.sectionNumber = sectionNumber;
    }

    public Double getArea() {
        return area;
    }

    public String getAreaFormatted() {
        return formatDouble(area);
    }

    public void setArea(Double area) {
        this.area = area;
    }

    public Double getAmountToBeCut() {
        return amountToBeCut;
    }

    public String getAmountToBeCutFormatted() {
        return formatDouble(amountToBeCut);
    }

    public void setAmountToBeCut(Double amountToBeCut) {
        this.amountToBeCut = amountToBeCut;
    }

    public String getTypeOfWork() {
        return typeOfWork;
    }

    public void setTypeOfWork(String typeOfWork) {
        this.typeOfWork = typeOfWork;
    }

    public String getNotificationId() {
        return notificationId;
    }

    public void setNotificationId(String notificationId) {
        this.notificationId = notificationId;
    }

    private String formatDouble(Double d) {
        if (d.intValue() == d) {
            return "" + d.intValue();
        }
        return DECIMAT_FORMAT_1_AFTER_COMMA.format(d);
    }
}
