
package rik.kinniskrteenused;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlType;


/**
 * <p>Java class for ObjektiAadress complex type.
 * 
 * <p>The following schema fragment specifies the expected content contained within this class.
 * 
 * <pre>
 * &lt;complexType name="ObjektiAadress">
 *   &lt;complexContent>
 *     &lt;restriction base="{http://www.w3.org/2001/XMLSchema}anyType">
 *       &lt;sequence>
 *         &lt;element name="koodaadress" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="taisaadress" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="adr_id" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="x_koordinaat" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="y_koordinaat" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *       &lt;/sequence>
 *     &lt;/restriction>
 *   &lt;/complexContent>
 * &lt;/complexType>
 * </pre>
 * 
 * 
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "ObjektiAadress", propOrder = {
    "koodaadress",
    "taisaadress",
    "adrId",
    "xKoordinaat",
    "yKoordinaat"
})
public class ObjektiAadress {

    protected String koodaadress;
    protected String taisaadress;
    @XmlElement(name = "adr_id")
    protected String adrId;
    @XmlElement(name = "x_koordinaat")
    protected String xKoordinaat;
    @XmlElement(name = "y_koordinaat")
    protected String yKoordinaat;

    /**
     * Gets the value of the koodaadress property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getKoodaadress() {
        return koodaadress;
    }

    /**
     * Sets the value of the koodaadress property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setKoodaadress(String value) {
        this.koodaadress = value;
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
     * Gets the value of the adrId property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getAdrId() {
        return adrId;
    }

    /**
     * Sets the value of the adrId property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setAdrId(String value) {
        this.adrId = value;
    }

    /**
     * Gets the value of the xKoordinaat property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getXKoordinaat() {
        return xKoordinaat;
    }

    /**
     * Sets the value of the xKoordinaat property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setXKoordinaat(String value) {
        this.xKoordinaat = value;
    }

    /**
     * Gets the value of the yKoordinaat property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getYKoordinaat() {
        return yKoordinaat;
    }

    /**
     * Sets the value of the yKoordinaat property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setYKoordinaat(String value) {
        this.yKoordinaat = value;
    }

}
