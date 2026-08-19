
package rik.kinniskrteenused;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlType;


/**
 * <p>Java class for Avaldus complex type.
 * 
 * <p>The following schema fragment specifies the expected content contained within this class.
 * 
 * <pre>
 * &lt;complexType name="Avaldus">
 *   &lt;complexContent>
 *     &lt;restriction base="{http://www.w3.org/2001/XMLSchema}anyType">
 *       &lt;sequence>
 *         &lt;element name="avalduse_nr" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="registreeritud_kp" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="esitaja_nimi" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="tehingu_nr" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="avalduse_esitaja_liik" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="markus" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="avalduse_liik" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *       &lt;/sequence>
 *     &lt;/restriction>
 *   &lt;/complexContent>
 * &lt;/complexType>
 * </pre>
 * 
 * 
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "Avaldus", propOrder = {
    "avalduseNr",
    "registreeritudKp",
    "esitajaNimi",
    "tehinguNr",
    "avalduseEsitajaLiik",
    "markus",
    "avalduseLiik"
})
public class Avaldus {

    @XmlElement(name = "avalduse_nr")
    protected String avalduseNr;
    @XmlElement(name = "registreeritud_kp")
    protected String registreeritudKp;
    @XmlElement(name = "esitaja_nimi")
    protected String esitajaNimi;
    @XmlElement(name = "tehingu_nr")
    protected String tehinguNr;
    @XmlElement(name = "avalduse_esitaja_liik")
    protected String avalduseEsitajaLiik;
    protected String markus;
    @XmlElement(name = "avalduse_liik")
    protected String avalduseLiik;

    /**
     * Gets the value of the avalduseNr property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getAvalduseNr() {
        return avalduseNr;
    }

    /**
     * Sets the value of the avalduseNr property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setAvalduseNr(String value) {
        this.avalduseNr = value;
    }

    /**
     * Gets the value of the registreeritudKp property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getRegistreeritudKp() {
        return registreeritudKp;
    }

    /**
     * Sets the value of the registreeritudKp property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setRegistreeritudKp(String value) {
        this.registreeritudKp = value;
    }

    /**
     * Gets the value of the esitajaNimi property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getEsitajaNimi() {
        return esitajaNimi;
    }

    /**
     * Sets the value of the esitajaNimi property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setEsitajaNimi(String value) {
        this.esitajaNimi = value;
    }

    /**
     * Gets the value of the tehinguNr property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getTehinguNr() {
        return tehinguNr;
    }

    /**
     * Sets the value of the tehinguNr property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setTehinguNr(String value) {
        this.tehinguNr = value;
    }

    /**
     * Gets the value of the avalduseEsitajaLiik property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getAvalduseEsitajaLiik() {
        return avalduseEsitajaLiik;
    }

    /**
     * Sets the value of the avalduseEsitajaLiik property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setAvalduseEsitajaLiik(String value) {
        this.avalduseEsitajaLiik = value;
    }

    /**
     * Gets the value of the markus property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getMarkus() {
        return markus;
    }

    /**
     * Sets the value of the markus property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setMarkus(String value) {
        this.markus = value;
    }

    /**
     * Gets the value of the avalduseLiik property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getAvalduseLiik() {
        return avalduseLiik;
    }

    /**
     * Sets the value of the avalduseLiik property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setAvalduseLiik(String value) {
        this.avalduseLiik = value;
    }

}
