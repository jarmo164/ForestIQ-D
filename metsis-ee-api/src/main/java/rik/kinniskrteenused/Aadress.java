
package rik.kinniskrteenused;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlType;


/**
 * <p>Java class for Aadress complex type.
 * 
 * <p>The following schema fragment specifies the expected content contained within this class.
 * 
 * <pre>
 * &lt;complexType name="Aadress">
 *   &lt;complexContent>
 *     &lt;restriction base="{http://www.w3.org/2001/XMLSchema}anyType">
 *       &lt;sequence>
 *         &lt;element name="aadress_haldusyksus" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="aadress_tanav" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="riik" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="ehak" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="aadress_objekt" type="{http://kinnistusraamat.rik.ee/krteenused/}AadressObjekt" minOccurs="0"/>
 *       &lt;/sequence>
 *     &lt;/restriction>
 *   &lt;/complexContent>
 * &lt;/complexType>
 * </pre>
 * 
 * 
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "Aadress", propOrder = {
    "aadressHaldusyksus",
    "aadressTanav",
    "riik",
    "ehak",
    "aadressObjekt"
})
public class Aadress {

    @XmlElement(name = "aadress_haldusyksus")
    protected String aadressHaldusyksus;
    @XmlElement(name = "aadress_tanav")
    protected String aadressTanav;
    protected String riik;
    protected String ehak;
    @XmlElement(name = "aadress_objekt")
    protected AadressObjekt aadressObjekt;

    /**
     * Gets the value of the aadressHaldusyksus property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getAadressHaldusyksus() {
        return aadressHaldusyksus;
    }

    /**
     * Sets the value of the aadressHaldusyksus property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setAadressHaldusyksus(String value) {
        this.aadressHaldusyksus = value;
    }

    /**
     * Gets the value of the aadressTanav property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getAadressTanav() {
        return aadressTanav;
    }

    /**
     * Sets the value of the aadressTanav property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setAadressTanav(String value) {
        this.aadressTanav = value;
    }

    /**
     * Gets the value of the riik property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getRiik() {
        return riik;
    }

    /**
     * Sets the value of the riik property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setRiik(String value) {
        this.riik = value;
    }

    /**
     * Gets the value of the ehak property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getEhak() {
        return ehak;
    }

    /**
     * Sets the value of the ehak property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setEhak(String value) {
        this.ehak = value;
    }

    /**
     * Gets the value of the aadressObjekt property.
     * 
     * @return
     *     possible object is
     *     {@link AadressObjekt }
     *     
     */
    public AadressObjekt getAadressObjekt() {
        return aadressObjekt;
    }

    /**
     * Sets the value of the aadressObjekt property.
     * 
     * @param value
     *     allowed object is
     *     {@link AadressObjekt }
     *     
     */
    public void setAadressObjekt(AadressObjekt value) {
        this.aadressObjekt = value;
    }

}
