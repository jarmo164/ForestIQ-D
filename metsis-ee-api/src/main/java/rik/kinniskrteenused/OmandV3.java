
package rik.kinniskrteenused;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlType;


/**
 * <p>Java class for OmandV3 complex type.
 * 
 * <p>The following schema fragment specifies the expected content contained within this class.
 * 
 * <pre>
 * &lt;complexType name="OmandV3">
 *   &lt;complexContent>
 *     &lt;restriction base="{http://www.w3.org/2001/XMLSchema}anyType">
 *       &lt;sequence>
 *         &lt;element name="isikud" type="{http://kinnistusraamat.rik.ee/krteenused/}ArrayOfIsikV3" minOccurs="0"/>
 *         &lt;element name="omandi_liik" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="omandiosa_lugeja" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="omandiosa_nimetaja" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="isik_omandis" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="paranduskanne" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="omandi_algus_kp" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="omandi_lopp_kp" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="omandiosa_nr" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *       &lt;/sequence>
 *     &lt;/restriction>
 *   &lt;/complexContent>
 * &lt;/complexType>
 * </pre>
 * 
 * 
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "OmandV3", propOrder = {
    "isikud",
    "omandiLiik",
    "omandiosaLugeja",
    "omandiosaNimetaja",
    "isikOmandis",
    "paranduskanne",
    "omandiAlgusKp",
    "omandiLoppKp",
    "omandiosaNr"
})
public class OmandV3 {

    protected ArrayOfIsikV3 isikud;
    @XmlElement(name = "omandi_liik")
    protected String omandiLiik;
    @XmlElement(name = "omandiosa_lugeja")
    protected String omandiosaLugeja;
    @XmlElement(name = "omandiosa_nimetaja")
    protected String omandiosaNimetaja;
    @XmlElement(name = "isik_omandis")
    protected String isikOmandis;
    protected String paranduskanne;
    @XmlElement(name = "omandi_algus_kp")
    protected String omandiAlgusKp;
    @XmlElement(name = "omandi_lopp_kp")
    protected String omandiLoppKp;
    @XmlElement(name = "omandiosa_nr")
    protected String omandiosaNr;

    /**
     * Gets the value of the isikud property.
     * 
     * @return
     *     possible object is
     *     {@link ArrayOfIsikV3 }
     *     
     */
    public ArrayOfIsikV3 getIsikud() {
        return isikud;
    }

    /**
     * Sets the value of the isikud property.
     * 
     * @param value
     *     allowed object is
     *     {@link ArrayOfIsikV3 }
     *     
     */
    public void setIsikud(ArrayOfIsikV3 value) {
        this.isikud = value;
    }

    /**
     * Gets the value of the omandiLiik property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getOmandiLiik() {
        return omandiLiik;
    }

    /**
     * Sets the value of the omandiLiik property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setOmandiLiik(String value) {
        this.omandiLiik = value;
    }

    /**
     * Gets the value of the omandiosaLugeja property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getOmandiosaLugeja() {
        return omandiosaLugeja;
    }

    /**
     * Sets the value of the omandiosaLugeja property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setOmandiosaLugeja(String value) {
        this.omandiosaLugeja = value;
    }

    /**
     * Gets the value of the omandiosaNimetaja property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getOmandiosaNimetaja() {
        return omandiosaNimetaja;
    }

    /**
     * Sets the value of the omandiosaNimetaja property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setOmandiosaNimetaja(String value) {
        this.omandiosaNimetaja = value;
    }

    /**
     * Gets the value of the isikOmandis property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getIsikOmandis() {
        return isikOmandis;
    }

    /**
     * Sets the value of the isikOmandis property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setIsikOmandis(String value) {
        this.isikOmandis = value;
    }

    /**
     * Gets the value of the paranduskanne property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getParanduskanne() {
        return paranduskanne;
    }

    /**
     * Sets the value of the paranduskanne property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setParanduskanne(String value) {
        this.paranduskanne = value;
    }

    /**
     * Gets the value of the omandiAlgusKp property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getOmandiAlgusKp() {
        return omandiAlgusKp;
    }

    /**
     * Sets the value of the omandiAlgusKp property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setOmandiAlgusKp(String value) {
        this.omandiAlgusKp = value;
    }

    /**
     * Gets the value of the omandiLoppKp property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getOmandiLoppKp() {
        return omandiLoppKp;
    }

    /**
     * Sets the value of the omandiLoppKp property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setOmandiLoppKp(String value) {
        this.omandiLoppKp = value;
    }

    /**
     * Gets the value of the omandiosaNr property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getOmandiosaNr() {
        return omandiosaNr;
    }

    /**
     * Sets the value of the omandiosaNr property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setOmandiosaNr(String value) {
        this.omandiosaNr = value;
    }

}
