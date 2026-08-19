
package rik.kinniskrteenused;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlType;


/**
 * <p>Java class for KinnistuV2 complex type.
 * 
 * <p>The following schema fragment specifies the expected content contained within this class.
 * 
 * <pre>
 * &lt;complexType name="KinnistuV2">
 *   &lt;complexContent>
 *     &lt;restriction base="{http://www.w3.org/2001/XMLSchema}anyType">
 *       &lt;sequence>
 *         &lt;element name="registriosa_uus_nr" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="registriosa_vana_nr" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="oiguse_marge" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="jaoskond" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="kinnistu_liik" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="kinnistu_nimi" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="korteri_nr" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="digitaalne_toimik" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="digitaalne_kp" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="ReaalosaAadressobjektid" type="{http://kinnistusraamat.rik.ee/krteenused/}ArrayOfAadressObjekt" minOccurs="0"/>
 *       &lt;/sequence>
 *     &lt;/restriction>
 *   &lt;/complexContent>
 * &lt;/complexType>
 * </pre>
 * 
 * 
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "KinnistuV2", propOrder = {
    "registriosaUusNr",
    "registriosaVanaNr",
    "oiguseMarge",
    "jaoskond",
    "kinnistuLiik",
    "kinnistuNimi",
    "korteriNr",
    "digitaalneToimik",
    "digitaalneKp",
    "reaalosaAadressobjektid"
})
public class KinnistuV2 {

    @XmlElement(name = "registriosa_uus_nr")
    protected String registriosaUusNr;
    @XmlElement(name = "registriosa_vana_nr")
    protected String registriosaVanaNr;
    @XmlElement(name = "oiguse_marge")
    protected String oiguseMarge;
    protected String jaoskond;
    @XmlElement(name = "kinnistu_liik")
    protected String kinnistuLiik;
    @XmlElement(name = "kinnistu_nimi")
    protected String kinnistuNimi;
    @XmlElement(name = "korteri_nr")
    protected String korteriNr;
    @XmlElement(name = "digitaalne_toimik")
    protected String digitaalneToimik;
    @XmlElement(name = "digitaalne_kp")
    protected String digitaalneKp;
    @XmlElement(name = "ReaalosaAadressobjektid")
    protected ArrayOfAadressObjekt reaalosaAadressobjektid;

    /**
     * Gets the value of the registriosaUusNr property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getRegistriosaUusNr() {
        return registriosaUusNr;
    }

    /**
     * Sets the value of the registriosaUusNr property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setRegistriosaUusNr(String value) {
        this.registriosaUusNr = value;
    }

    /**
     * Gets the value of the registriosaVanaNr property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getRegistriosaVanaNr() {
        return registriosaVanaNr;
    }

    /**
     * Sets the value of the registriosaVanaNr property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setRegistriosaVanaNr(String value) {
        this.registriosaVanaNr = value;
    }

    /**
     * Gets the value of the oiguseMarge property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getOiguseMarge() {
        return oiguseMarge;
    }

    /**
     * Sets the value of the oiguseMarge property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setOiguseMarge(String value) {
        this.oiguseMarge = value;
    }

    /**
     * Gets the value of the jaoskond property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getJaoskond() {
        return jaoskond;
    }

    /**
     * Sets the value of the jaoskond property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setJaoskond(String value) {
        this.jaoskond = value;
    }

    /**
     * Gets the value of the kinnistuLiik property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getKinnistuLiik() {
        return kinnistuLiik;
    }

    /**
     * Sets the value of the kinnistuLiik property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setKinnistuLiik(String value) {
        this.kinnistuLiik = value;
    }

    /**
     * Gets the value of the kinnistuNimi property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getKinnistuNimi() {
        return kinnistuNimi;
    }

    /**
     * Sets the value of the kinnistuNimi property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setKinnistuNimi(String value) {
        this.kinnistuNimi = value;
    }

    /**
     * Gets the value of the korteriNr property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getKorteriNr() {
        return korteriNr;
    }

    /**
     * Sets the value of the korteriNr property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setKorteriNr(String value) {
        this.korteriNr = value;
    }

    /**
     * Gets the value of the digitaalneToimik property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getDigitaalneToimik() {
        return digitaalneToimik;
    }

    /**
     * Sets the value of the digitaalneToimik property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setDigitaalneToimik(String value) {
        this.digitaalneToimik = value;
    }

    /**
     * Gets the value of the digitaalneKp property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getDigitaalneKp() {
        return digitaalneKp;
    }

    /**
     * Sets the value of the digitaalneKp property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setDigitaalneKp(String value) {
        this.digitaalneKp = value;
    }

    /**
     * Gets the value of the reaalosaAadressobjektid property.
     * 
     * @return
     *     possible object is
     *     {@link ArrayOfAadressObjekt }
     *     
     */
    public ArrayOfAadressObjekt getReaalosaAadressobjektid() {
        return reaalosaAadressobjektid;
    }

    /**
     * Sets the value of the reaalosaAadressobjektid property.
     * 
     * @param value
     *     allowed object is
     *     {@link ArrayOfAadressObjekt }
     *     
     */
    public void setReaalosaAadressobjektid(ArrayOfAadressObjekt value) {
        this.reaalosaAadressobjektid = value;
    }

}
