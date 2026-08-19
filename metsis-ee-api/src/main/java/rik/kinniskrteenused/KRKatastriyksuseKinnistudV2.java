
package rik.kinniskrteenused;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
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
 *         &lt;element name="katastritunnus" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
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
    "katastritunnus",
    "kasutajanimi",
    "parool"
})
@XmlRootElement(name = "KR_katastriyksuse_kinnistud_v2")
public class KRKatastriyksuseKinnistudV2 {

    protected String katastritunnus;
    protected String kasutajanimi;
    protected String parool;

    /**
     * Gets the value of the katastritunnus property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getKatastritunnus() {
        return katastritunnus;
    }

    /**
     * Sets the value of the katastritunnus property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setKatastritunnus(String value) {
        this.katastritunnus = value;
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
