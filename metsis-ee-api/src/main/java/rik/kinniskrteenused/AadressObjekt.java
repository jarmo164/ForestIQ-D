
package rik.kinniskrteenused;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlType;


/**
 * <p>Java class for AadressObjekt complex type.
 * 
 * <p>The following schema fragment specifies the expected content contained within this class.
 * 
 * <pre>
 * &lt;complexType name="AadressObjekt">
 *   &lt;complexContent>
 *     &lt;restriction base="{http://www.w3.org/2001/XMLSchema}anyType">
 *       &lt;sequence>
 *         &lt;element name="ads_oid" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="taisaadress" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="objekti_aadressid" type="{http://kinnistusraamat.rik.ee/krteenused/}ArrayOfObjektiAadress" minOccurs="0"/>
 *       &lt;/sequence>
 *     &lt;/restriction>
 *   &lt;/complexContent>
 * &lt;/complexType>
 * </pre>
 * 
 * 
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "AadressObjekt", propOrder = {
    "adsOid",
    "taisaadress",
    "objektiAadressid"
})
public class AadressObjekt {

    @XmlElement(name = "ads_oid")
    protected String adsOid;
    protected String taisaadress;
    @XmlElement(name = "objekti_aadressid")
    protected ArrayOfObjektiAadress objektiAadressid;

    /**
     * Gets the value of the adsOid property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getAdsOid() {
        return adsOid;
    }

    /**
     * Sets the value of the adsOid property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setAdsOid(String value) {
        this.adsOid = value;
    }

    /**
     * Gets the value of the taisaadress property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getTaisaadress() {
        return taisaadress;
    }

    /**
     * Sets the value of the taisaadress property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setTaisaadress(String value) {
        this.taisaadress = value;
    }

    /**
     * Gets the value of the objektiAadressid property.
     * 
     * @return
     *     possible object is
     *     {@link ArrayOfObjektiAadress }
     *     
     */
    public ArrayOfObjektiAadress getObjektiAadressid() {
        return objektiAadressid;
    }

    /**
     * Sets the value of the objektiAadressid property.
     * 
     * @param value
     *     allowed object is
     *     {@link ArrayOfObjektiAadress }
     *     
     */
    public void setObjektiAadressid(ArrayOfObjektiAadress value) {
        this.objektiAadressid = value;
    }

}
