
package rik.kinniskrteenused;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlType;


/**
 * <p>Java class for Isiku_kood complex type.
 * 
 * <p>The following schema fragment specifies the expected content contained within this class.
 * 
 * <pre>
 * &lt;complexType name="Isiku_kood">
 *   &lt;complexContent>
 *     &lt;restriction base="{http://www.w3.org/2001/XMLSchema}anyType">
 *       &lt;sequence>
 *         &lt;element name="isiku_kood" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="valjaandja_riik" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *       &lt;/sequence>
 *     &lt;/restriction>
 *   &lt;/complexContent>
 * &lt;/complexType>
 * </pre>
 * 
 * 
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "Isiku_kood", propOrder = {
    "isikuKood",
    "valjaandjaRiik"
})
public class IsikuKood {

    @XmlElement(name = "isiku_kood")
    protected String isikuKood;
    @XmlElement(name = "valjaandja_riik")
    protected String valjaandjaRiik;

    /**
     * Gets the value of the isikuKood property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getIsikuKood() {
        return isikuKood;
    }

    /**
     * Sets the value of the isikuKood property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setIsikuKood(String value) {
        this.isikuKood = value;
    }

    /**
     * Gets the value of the valjaandjaRiik property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getValjaandjaRiik() {
        return valjaandjaRiik;
    }

    /**
     * Sets the value of the valjaandjaRiik property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setValjaandjaRiik(String value) {
        this.valjaandjaRiik = value;
    }

}
