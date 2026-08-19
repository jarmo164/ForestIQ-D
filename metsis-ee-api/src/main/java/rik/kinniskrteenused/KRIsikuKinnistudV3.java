
package rik.kinniskrteenused;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlType;


/**
 * <p>Java class for KR_Isiku_kinnistudV3 complex type.
 * 
 * <p>The following schema fragment specifies the expected content contained within this class.
 * 
 * <pre>
 * &lt;complexType name="KR_Isiku_kinnistudV3">
 *   &lt;complexContent>
 *     &lt;restriction base="{http://www.w3.org/2001/XMLSchema}anyType">
 *       &lt;sequence>
 *         &lt;element name="veateade" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="systeemiteade" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="kinnistud" type="{http://kinnistusraamat.rik.ee/krteenused/}ArrayOfKinnistuV3" minOccurs="0"/>
 *       &lt;/sequence>
 *     &lt;/restriction>
 *   &lt;/complexContent>
 * &lt;/complexType>
 * </pre>
 * 
 * 
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "KR_Isiku_kinnistudV3", propOrder = {
    "veateade",
    "systeemiteade",
    "kinnistud"
})
public class KRIsikuKinnistudV3 {

    protected String veateade;
    protected String systeemiteade;
    protected ArrayOfKinnistuV3 kinnistud;

    /**
     * Gets the value of the veateade property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getVeateade() {
        return veateade;
    }

    /**
     * Sets the value of the veateade property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setVeateade(String value) {
        this.veateade = value;
    }

    /**
     * Gets the value of the systeemiteade property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getSysteemiteade() {
        return systeemiteade;
    }

    /**
     * Sets the value of the systeemiteade property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setSysteemiteade(String value) {
        this.systeemiteade = value;
    }

    /**
     * Gets the value of the kinnistud property.
     * 
     * @return
     *     possible object is
     *     {@link ArrayOfKinnistuV3 }
     *     
     */
    public ArrayOfKinnistuV3 getKinnistud() {
        return kinnistud;
    }

    /**
     * Sets the value of the kinnistud property.
     * 
     * @param value
     *     allowed object is
     *     {@link ArrayOfKinnistuV3 }
     *     
     */
    public void setKinnistud(ArrayOfKinnistuV3 value) {
        this.kinnistud = value;
    }

}
