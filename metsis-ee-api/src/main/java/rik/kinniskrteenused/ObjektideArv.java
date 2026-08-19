
package rik.kinniskrteenused;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlType;


/**
 * <p>Java class for Objektide_arv complex type.
 * 
 * <p>The following schema fragment specifies the expected content contained within this class.
 * 
 * <pre>
 * &lt;complexType name="Objektide_arv">
 *   &lt;complexContent>
 *     &lt;restriction base="{http://www.w3.org/2001/XMLSchema}anyType">
 *       &lt;sequence>
 *         &lt;element name="veateade" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="systeemiteade" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="arv" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *       &lt;/sequence>
 *     &lt;/restriction>
 *   &lt;/complexContent>
 * &lt;/complexType>
 * </pre>
 * 
 * 
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "Objektide_arv", propOrder = {
    "veateade",
    "systeemiteade",
    "arv"
})
public class ObjektideArv {

    protected String veateade;
    protected String systeemiteade;
    protected String arv;

    /**
     * Gets the value of the veateade property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getVeateade() {
        return veateade;
    }

    /**
     * Sets the value of the veateade property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setVeateade(String value) {
        this.veateade = value;
    }

    /**
     * Gets the value of the systeemiteade property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getSysteemiteade() {
        return systeemiteade;
    }

    /**
     * Sets the value of the systeemiteade property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setSysteemiteade(String value) {
        this.systeemiteade = value;
    }

    /**
     * Gets the value of the arv property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getArv() {
        return arv;
    }

    /**
     * Sets the value of the arv property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setArv(String value) {
        this.arv = value;
    }

}
