
package rik.kinniskrteenused;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlType;


/**
 * <p>Java class for Isik complex type.
 * 
 * <p>The following schema fragment specifies the expected content contained within this class.
 * 
 * <pre>
 * &lt;complexType name="Isik">
 *   &lt;complexContent>
 *     &lt;restriction base="{http://www.w3.org/2001/XMLSchema}anyType">
 *       &lt;sequence>
 *         &lt;element name="isiku_liik" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="eesnimi" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="perenimi_firma" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="synniaeg" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="isikukoodid" type="{http://kinnistusraamat.rik.ee/krteenused/}ArrayOfIsiku_kood" minOccurs="0"/>
 *       &lt;/sequence>
 *     &lt;/restriction>
 *   &lt;/complexContent>
 * &lt;/complexType>
 * </pre>
 * 
 * 
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "Isik", propOrder = {
    "isikuLiik",
    "eesnimi",
    "perenimiFirma",
    "synniaeg",
    "isikukoodid"
})
public class Isik {

    @XmlElement(name = "isiku_liik")
    protected String isikuLiik;
    protected String eesnimi;
    @XmlElement(name = "perenimi_firma")
    protected String perenimiFirma;
    protected String synniaeg;
    protected ArrayOfIsikuKood isikukoodid;

    /**
     * Gets the value of the isikuLiik property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getIsikuLiik() {
        return isikuLiik;
    }

    /**
     * Sets the value of the isikuLiik property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setIsikuLiik(String value) {
        this.isikuLiik = value;
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
     * Gets the value of the synniaeg property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getSynniaeg() {
        return synniaeg;
    }

    /**
     * Sets the value of the synniaeg property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setSynniaeg(String value) {
        this.synniaeg = value;
    }

    /**
     * Gets the value of the isikukoodid property.
     * 
     * @return
     *     possible object is
     *     {@link ArrayOfIsikuKood }
     *     
     */
    public ArrayOfIsikuKood getIsikukoodid() {
        return isikukoodid;
    }

    /**
     * Sets the value of the isikukoodid property.
     * 
     * @param value
     *     allowed object is
     *     {@link ArrayOfIsikuKood }
     *     
     */
    public void setIsikukoodid(ArrayOfIsikuKood value) {
        this.isikukoodid = value;
    }

}
