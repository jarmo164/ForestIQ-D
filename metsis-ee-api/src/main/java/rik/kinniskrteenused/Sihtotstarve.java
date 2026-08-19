
package rik.kinniskrteenused;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlType;


/**
 * <p>Java class for Sihtotstarve complex type.
 * 
 * <p>The following schema fragment specifies the expected content contained within this class.
 * 
 * <pre>
 * &lt;complexType name="Sihtotstarve">
 *   &lt;complexContent>
 *     &lt;restriction base="{http://www.w3.org/2001/XMLSchema}anyType">
 *       &lt;sequence>
 *         &lt;element name="sihtotstarve" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="sihtotstarve_protsent" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *       &lt;/sequence>
 *     &lt;/restriction>
 *   &lt;/complexContent>
 * &lt;/complexType>
 * </pre>
 * 
 * 
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "Sihtotstarve", propOrder = {
    "sihtotstarve",
    "sihtotstarveProtsent"
})
public class Sihtotstarve {

    protected String sihtotstarve;
    @XmlElement(name = "sihtotstarve_protsent")
    protected String sihtotstarveProtsent;

    /**
     * Gets the value of the sihtotstarve property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getSihtotstarve() {
        return sihtotstarve;
    }

    /**
     * Sets the value of the sihtotstarve property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setSihtotstarve(String value) {
        this.sihtotstarve = value;
    }

    /**
     * Gets the value of the sihtotstarveProtsent property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getSihtotstarveProtsent() {
        return sihtotstarveProtsent;
    }

    /**
     * Sets the value of the sihtotstarveProtsent property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setSihtotstarveProtsent(String value) {
        this.sihtotstarveProtsent = value;
    }

}
