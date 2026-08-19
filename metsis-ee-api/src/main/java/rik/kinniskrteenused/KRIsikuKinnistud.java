
package rik.kinniskrteenused;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlType;


/**
 * <p>Java class for KR_Isiku_kinnistud complex type.
 * 
 * <p>The following schema fragment specifies the expected content contained within this class.
 * 
 * <pre>
 * &lt;complexType name="KR_Isiku_kinnistud">
 *   &lt;complexContent>
 *     &lt;restriction base="{http://www.w3.org/2001/XMLSchema}anyType">
 *       &lt;sequence>
 *         &lt;element name="veateade" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="systeemiteade" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="kinnistud" type="{http://kinnistusraamat.rik.ee/krteenused/}ArrayOfKinnistu" minOccurs="0"/>
 *       &lt;/sequence>
 *     &lt;/restriction>
 *   &lt;/complexContent>
 * &lt;/complexType>
 * </pre>
 * 
 * 
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "KR_Isiku_kinnistud", propOrder = {
    "veateade",
    "systeemiteade",
    "kinnistud"
})
public class KRIsikuKinnistud {

    protected String veateade;
    protected String systeemiteade;
    protected ArrayOfKinnistu kinnistud;

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
     *     {@link ArrayOfKinnistu }
     *     
     */
    public ArrayOfKinnistu getKinnistud() {
        return kinnistud;
    }

    /**
     * Sets the value of the kinnistud property.
     * 
     * @param value
     *     allowed object is
     *     {@link ArrayOfKinnistu }
     *     
     */
    public void setKinnistud(ArrayOfKinnistu value) {
        this.kinnistud = value;
    }

}
