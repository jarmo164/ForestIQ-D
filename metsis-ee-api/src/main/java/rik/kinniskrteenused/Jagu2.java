
package rik.kinniskrteenused;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlType;


/**
 * <p>Java class for Jagu_2 complex type.
 * 
 * <p>The following schema fragment specifies the expected content contained within this class.
 * 
 * <pre>
 * &lt;complexType name="Jagu_2">
 *   &lt;complexContent>
 *     &lt;restriction base="{http://www.w3.org/2001/XMLSchema}anyType">
 *       &lt;sequence>
 *         &lt;element name="kandetekst" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="kande_nr" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="omandid" type="{http://kinnistusraamat.rik.ee/krteenused/}ArrayOfOmand" minOccurs="0"/>
 *         &lt;element name="kehtivus" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
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
@XmlType(name = "Jagu_2", propOrder = {
    "kandetekst",
    "kandeNr",
    "omandid",
    "kehtivus",
    "kandeLiik"
})
public class Jagu2 {

    protected String kandetekst;
    @XmlElement(name = "kande_nr")
    protected String kandeNr;
    protected ArrayOfOmand omandid;
    protected String kehtivus;
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
     * Gets the value of the omandid property.
     * 
     * @return
     *     possible object is
     *     {@link ArrayOfOmand }
     *     
     */
    public ArrayOfOmand getOmandid() {
        return omandid;
    }

    /**
     * Sets the value of the omandid property.
     * 
     * @param value
     *     allowed object is
     *     {@link ArrayOfOmand }
     *     
     */
    public void setOmandid(ArrayOfOmand value) {
        this.omandid = value;
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
