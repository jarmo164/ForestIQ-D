
package rik.kinniskrteenused;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlType;


/**
 * <p>Java class for Reaalosa_infoV2 complex type.
 * 
 * <p>The following schema fragment specifies the expected content contained within this class.
 * 
 * <pre>
 * &lt;complexType name="Reaalosa_infoV2">
 *   &lt;complexContent>
 *     &lt;restriction base="{http://www.w3.org/2001/XMLSchema}anyType">
 *       &lt;sequence>
 *         &lt;element name="nr" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="tahistus_plaanil" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="liik" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="yldpind" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="motteline_osa" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="Aadressobjektid" type="{http://kinnistusraamat.rik.ee/krteenused/}ArrayOfAadressObjekt" minOccurs="0"/>
 *       &lt;/sequence>
 *     &lt;/restriction>
 *   &lt;/complexContent>
 * &lt;/complexType>
 * </pre>
 * 
 * 
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "Reaalosa_infoV2", propOrder = {
    "nr",
    "tahistusPlaanil",
    "liik",
    "yldpind",
    "mottelineOsa",
    "aadressobjektid"
})
public class ReaalosaInfoV2 {

    protected String nr;
    @XmlElement(name = "tahistus_plaanil")
    protected String tahistusPlaanil;
    protected String liik;
    protected String yldpind;
    @XmlElement(name = "motteline_osa")
    protected String mottelineOsa;
    @XmlElement(name = "Aadressobjektid")
    protected ArrayOfAadressObjekt aadressobjektid;

    /**
     * Gets the value of the nr property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getNr() {
        return nr;
    }

    /**
     * Sets the value of the nr property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setNr(String value) {
        this.nr = value;
    }

    /**
     * Gets the value of the tahistusPlaanil property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getTahistusPlaanil() {
        return tahistusPlaanil;
    }

    /**
     * Sets the value of the tahistusPlaanil property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setTahistusPlaanil(String value) {
        this.tahistusPlaanil = value;
    }

    /**
     * Gets the value of the liik property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getLiik() {
        return liik;
    }

    /**
     * Sets the value of the liik property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setLiik(String value) {
        this.liik = value;
    }

    /**
     * Gets the value of the yldpind property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getYldpind() {
        return yldpind;
    }

    /**
     * Sets the value of the yldpind property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setYldpind(String value) {
        this.yldpind = value;
    }

    /**
     * Gets the value of the mottelineOsa property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getMottelineOsa() {
        return mottelineOsa;
    }

    /**
     * Sets the value of the mottelineOsa property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setMottelineOsa(String value) {
        this.mottelineOsa = value;
    }

    /**
     * Gets the value of the aadressobjektid property.
     * 
     * @return
     *     possible object is
     *     {@link ArrayOfAadressObjekt }
     *     
     */
    public ArrayOfAadressObjekt getAadressobjektid() {
        return aadressobjektid;
    }

    /**
     * Sets the value of the aadressobjektid property.
     * 
     * @param value
     *     allowed object is
     *     {@link ArrayOfAadressObjekt }
     *     
     */
    public void setAadressobjektid(ArrayOfAadressObjekt value) {
        this.aadressobjektid = value;
    }

}
