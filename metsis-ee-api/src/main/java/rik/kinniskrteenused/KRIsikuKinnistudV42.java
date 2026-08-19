
package rik.kinniskrteenused;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlRootElement;
import javax.xml.bind.annotation.XmlType;


/**
 * <p>Java class for anonymous complex type.
 * 
 * <p>The following schema fragment specifies the expected content contained within this class.
 * 
 * <pre>
 * &lt;complexType>
 *   &lt;complexContent>
 *     &lt;restriction base="{http://www.w3.org/2001/XMLSchema}anyType">
 *       &lt;sequence>
 *         &lt;element name="kood" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="eesnimi" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="perenimi_firma" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="kehtivad_kehtetud" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="kasutajanimi" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="parool" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *       &lt;/sequence>
 *     &lt;/restriction>
 *   &lt;/complexContent>
 * &lt;/complexType>
 * </pre>
 * 
 * 
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "", propOrder = {
    "kood",
    "eesnimi",
    "perenimiFirma",
    "kehtivadKehtetud",
    "kasutajanimi",
    "parool"
})
@XmlRootElement(name = "kR_isiku_kinnistud_v4")
public class KRIsikuKinnistudV42 {

    protected String kood;
    protected String eesnimi;
    @XmlElement(name = "perenimi_firma")
    protected String perenimiFirma;
    @XmlElement(name = "kehtivad_kehtetud")
    protected String kehtivadKehtetud;
    protected String kasutajanimi;
    protected String parool;

    /**
     * Gets the value of the kood property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getKood() {
        return kood;
    }

    /**
     * Sets the value of the kood property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setKood(String value) {
        this.kood = value;
    }

    /**
     * Gets the value of the eesnimi property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getEesnimi() {
        return eesnimi;
    }

    /**
     * Sets the value of the eesnimi property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setEesnimi(String value) {
        this.eesnimi = value;
    }

    /**
     * Gets the value of the perenimiFirma property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getPerenimiFirma() {
        return perenimiFirma;
    }

    /**
     * Sets the value of the perenimiFirma property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setPerenimiFirma(String value) {
        this.perenimiFirma = value;
    }

    /**
     * Gets the value of the kehtivadKehtetud property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getKehtivadKehtetud() {
        return kehtivadKehtetud;
    }

    /**
     * Sets the value of the kehtivadKehtetud property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setKehtivadKehtetud(String value) {
        this.kehtivadKehtetud = value;
    }

    /**
     * Gets the value of the kasutajanimi property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getKasutajanimi() {
        return kasutajanimi;
    }

    /**
     * Sets the value of the kasutajanimi property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setKasutajanimi(String value) {
        this.kasutajanimi = value;
    }

    /**
     * Gets the value of the parool property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getParool() {
        return parool;
    }

    /**
     * Sets the value of the parool property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setParool(String value) {
        this.parool = value;
    }

}
