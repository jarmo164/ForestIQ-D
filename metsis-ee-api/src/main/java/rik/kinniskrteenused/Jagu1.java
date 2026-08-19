
package rik.kinniskrteenused;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlType;


/**
 * <p>Java class for Jagu_1 complex type.
 * 
 * <p>The following schema fragment specifies the expected content contained within this class.
 * 
 * <pre>
 * &lt;complexType name="Jagu_1">
 *   &lt;complexContent>
 *     &lt;restriction base="{http://www.w3.org/2001/XMLSchema}anyType">
 *       &lt;sequence>
 *         &lt;element name="kandetekst" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="kandealus" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="kande_nr" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="katastriyksused" type="{http://kinnistusraamat.rik.ee/krteenused/}ArrayOfKatastriyksus" minOccurs="0"/>
 *         &lt;element name="reaalosade_info" type="{http://kinnistusraamat.rik.ee/krteenused/}ArrayOfReaalosa_info" minOccurs="0"/>
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
@XmlType(name = "Jagu_1", propOrder = {
    "kandetekst",
    "kandealus",
    "kandeNr",
    "katastriyksused",
    "reaalosadeInfo",
    "kehtivus",
    "kandeLiik"
})
public class Jagu1 {

    protected String kandetekst;
    protected String kandealus;
    @XmlElement(name = "kande_nr")
    protected String kandeNr;
    protected ArrayOfKatastriyksus katastriyksused;
    @XmlElement(name = "reaalosade_info")
    protected ArrayOfReaalosaInfo reaalosadeInfo;
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
     * Gets the value of the katastriyksused property.
     * 
     * @return
     *     possible object is
     *     {@link ArrayOfKatastriyksus }
     *     
     */
    public ArrayOfKatastriyksus getKatastriyksused() {
        return katastriyksused;
    }

    /**
     * Sets the value of the katastriyksused property.
     * 
     * @param value
     *     allowed object is
     *     {@link ArrayOfKatastriyksus }
     *     
     */
    public void setKatastriyksused(ArrayOfKatastriyksus value) {
        this.katastriyksused = value;
    }

    /**
     * Gets the value of the reaalosadeInfo property.
     * 
     * @return
     *     possible object is
     *     {@link ArrayOfReaalosaInfo }
     *     
     */
    public ArrayOfReaalosaInfo getReaalosadeInfo() {
        return reaalosadeInfo;
    }

    /**
     * Sets the value of the reaalosadeInfo property.
     * 
     * @param value
     *     allowed object is
     *     {@link ArrayOfReaalosaInfo }
     *     
     */
    public void setReaalosadeInfo(ArrayOfReaalosaInfo value) {
        this.reaalosadeInfo = value;
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
