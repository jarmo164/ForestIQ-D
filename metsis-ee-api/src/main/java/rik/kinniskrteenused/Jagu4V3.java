
package rik.kinniskrteenused;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlType;


/**
 * <p>Java class for Jagu_4V3 complex type.
 * 
 * <p>The following schema fragment specifies the expected content contained within this class.
 * 
 * <pre>
 * &lt;complexType name="Jagu_4V3">
 *   &lt;complexContent>
 *     &lt;restriction base="{http://www.w3.org/2001/XMLSchema}anyType">
 *       &lt;sequence>
 *         &lt;element name="kandetekst" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="kandealus" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="kande_nr" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="kande_alguskp" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="kande_loppkp" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="kehtivus" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="omandiosa_nr" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="kande_liik" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *       &lt;/sequence>
 *     &lt;/restriction>
 *   &lt;/complexContent>
 * &lt;/complexType>
 * </pre>
 * 
 * 
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "Jagu_4V3", propOrder = {
    "kandetekst",
    "kandealus",
    "kandeNr",
    "kandeAlguskp",
    "kandeLoppkp",
    "kehtivus",
    "omandiosaNr",
    "kandeLiik"
})
public class Jagu4V3 {

    protected String kandetekst;
    protected String kandealus;
    @XmlElement(name = "kande_nr")
    protected String kandeNr;
    @XmlElement(name = "kande_alguskp")
    protected String kandeAlguskp;
    @XmlElement(name = "kande_loppkp")
    protected String kandeLoppkp;
    protected String kehtivus;
    @XmlElement(name = "omandiosa_nr")
    protected String omandiosaNr;
    @XmlElement(name = "kande_liik")
    protected String kandeLiik;

    /**
     * Gets the value of the kandetekst property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getKandetekst() {
        return kandetekst;
    }

    /**
     * Sets the value of the kandetekst property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setKandetekst(String value) {
        this.kandetekst = value;
    }

    /**
     * Gets the value of the kandealus property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getKandealus() {
        return kandealus;
    }

    /**
     * Sets the value of the kandealus property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setKandealus(String value) {
        this.kandealus = value;
    }

    /**
     * Gets the value of the kandeNr property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getKandeNr() {
        return kandeNr;
    }

    /**
     * Sets the value of the kandeNr property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setKandeNr(String value) {
        this.kandeNr = value;
    }

    /**
     * Gets the value of the kandeAlguskp property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getKandeAlguskp() {
        return kandeAlguskp;
    }

    /**
     * Sets the value of the kandeAlguskp property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setKandeAlguskp(String value) {
        this.kandeAlguskp = value;
    }

    /**
     * Gets the value of the kandeLoppkp property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getKandeLoppkp() {
        return kandeLoppkp;
    }

    /**
     * Sets the value of the kandeLoppkp property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setKandeLoppkp(String value) {
        this.kandeLoppkp = value;
    }

    /**
     * Gets the value of the kehtivus property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getKehtivus() {
        return kehtivus;
    }

    /**
     * Sets the value of the kehtivus property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setKehtivus(String value) {
        this.kehtivus = value;
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

    /**
     * Gets the value of the kandeLiik property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getKandeLiik() {
        return kandeLiik;
    }

    /**
     * Sets the value of the kandeLiik property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setKandeLiik(String value) {
        this.kandeLiik = value;
    }

}
