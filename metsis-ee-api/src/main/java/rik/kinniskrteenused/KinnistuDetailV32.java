
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
 *         &lt;element name="registriosa_nr" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="kehtivad_kehtetud" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="kas_lisainfo" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="kogu_ro" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="jagu_1" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="jagu_2" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="jagu_3_4" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
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
    "registriosaNr",
    "kehtivadKehtetud",
    "kasLisainfo",
    "koguRo",
    "jagu1",
    "jagu2",
    "jagu34",
    "kasutajanimi",
    "parool"
})
@XmlRootElement(name = "kinnistu_detail_v3")
public class KinnistuDetailV32 {

    @XmlElement(name = "registriosa_nr")
    protected String registriosaNr;
    @XmlElement(name = "kehtivad_kehtetud")
    protected String kehtivadKehtetud;
    @XmlElement(name = "kas_lisainfo")
    protected String kasLisainfo;
    @XmlElement(name = "kogu_ro")
    protected String koguRo;
    @XmlElement(name = "jagu_1")
    protected String jagu1;
    @XmlElement(name = "jagu_2")
    protected String jagu2;
    @XmlElement(name = "jagu_3_4")
    protected String jagu34;
    protected String kasutajanimi;
    protected String parool;

    /**
     * Gets the value of the registriosaNr property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getRegistriosaNr() {
        return registriosaNr;
    }

    /**
     * Sets the value of the registriosaNr property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setRegistriosaNr(String value) {
        this.registriosaNr = value;
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
     * Gets the value of the kasLisainfo property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getKasLisainfo() {
        return kasLisainfo;
    }

    /**
     * Sets the value of the kasLisainfo property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setKasLisainfo(String value) {
        this.kasLisainfo = value;
    }

    /**
     * Gets the value of the koguRo property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getKoguRo() {
        return koguRo;
    }

    /**
     * Sets the value of the koguRo property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setKoguRo(String value) {
        this.koguRo = value;
    }

    /**
     * Gets the value of the jagu1 property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getJagu1() {
        return jagu1;
    }

    /**
     * Sets the value of the jagu1 property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setJagu1(String value) {
        this.jagu1 = value;
    }

    /**
     * Gets the value of the jagu2 property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getJagu2() {
        return jagu2;
    }

    /**
     * Sets the value of the jagu2 property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setJagu2(String value) {
        this.jagu2 = value;
    }

    /**
     * Gets the value of the jagu34 property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getJagu34() {
        return jagu34;
    }

    /**
     * Sets the value of the jagu34 property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setJagu34(String value) {
        this.jagu34 = value;
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
