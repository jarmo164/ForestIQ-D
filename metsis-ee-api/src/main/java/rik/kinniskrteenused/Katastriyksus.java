
package rik.kinniskrteenused;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlType;


/**
 * <p>Java class for Katastriyksus complex type.
 * 
 * <p>The following schema fragment specifies the expected content contained within this class.
 * 
 * <pre>
 * &lt;complexType name="Katastriyksus">
 *   &lt;complexContent>
 *     &lt;restriction base="{http://www.w3.org/2001/XMLSchema}anyType">
 *       &lt;sequence>
 *         &lt;element name="sihtotstarve" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="tunnus" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="juriidilineAadress" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="pindala" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="pindala_yhik" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="aadressid" type="{http://kinnistusraamat.rik.ee/krteenused/}ArrayOfAadress" minOccurs="0"/>
 *         &lt;element name="plaani_alusel" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="sihtotstarbed" type="{http://kinnistusraamat.rik.ee/krteenused/}ArrayOfSihtotstarve" minOccurs="0"/>
 *         &lt;element name="KatastriyksuseAadressObjektid" type="{http://kinnistusraamat.rik.ee/krteenused/}ArrayOfAadressObjekt" minOccurs="0"/>
 *       &lt;/sequence>
 *     &lt;/restriction>
 *   &lt;/complexContent>
 * &lt;/complexType>
 * </pre>
 * 
 * 
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "Katastriyksus", propOrder = {
    "sihtotstarve",
    "tunnus",
    "juriidilineAadress",
    "pindala",
    "pindalaYhik",
    "aadressid",
    "plaaniAlusel",
    "sihtotstarbed",
    "katastriyksuseAadressObjektid"
})
public class Katastriyksus {

    protected String sihtotstarve;
    protected String tunnus;
    protected String juriidilineAadress;
    protected String pindala;
    @XmlElement(name = "pindala_yhik")
    protected String pindalaYhik;
    protected ArrayOfAadress aadressid;
    @XmlElement(name = "plaani_alusel")
    protected String plaaniAlusel;
    protected ArrayOfSihtotstarve sihtotstarbed;
    @XmlElement(name = "KatastriyksuseAadressObjektid")
    protected ArrayOfAadressObjekt katastriyksuseAadressObjektid;

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
     * Gets the value of the tunnus property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getTunnus() {
        return tunnus;
    }

    /**
     * Sets the value of the tunnus property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setTunnus(String value) {
        this.tunnus = value;
    }

    /**
     * Gets the value of the juriidilineAadress property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getJuriidilineAadress() {
        return juriidilineAadress;
    }

    /**
     * Sets the value of the juriidilineAadress property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setJuriidilineAadress(String value) {
        this.juriidilineAadress = value;
    }

    /**
     * Gets the value of the pindala property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getPindala() {
        return pindala;
    }

    /**
     * Sets the value of the pindala property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setPindala(String value) {
        this.pindala = value;
    }

    /**
     * Gets the value of the pindalaYhik property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getPindalaYhik() {
        return pindalaYhik;
    }

    /**
     * Sets the value of the pindalaYhik property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setPindalaYhik(String value) {
        this.pindalaYhik = value;
    }

    /**
     * Gets the value of the aadressid property.
     * 
     * @return
     *     possible object is
     *     {@link ArrayOfAadress }
     *     
     */
    public ArrayOfAadress getAadressid() {
        return aadressid;
    }

    /**
     * Sets the value of the aadressid property.
     * 
     * @param value
     *     allowed object is
     *     {@link ArrayOfAadress }
     *     
     */
    public void setAadressid(ArrayOfAadress value) {
        this.aadressid = value;
    }

    /**
     * Gets the value of the plaaniAlusel property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getPlaaniAlusel() {
        return plaaniAlusel;
    }

    /**
     * Sets the value of the plaaniAlusel property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setPlaaniAlusel(String value) {
        this.plaaniAlusel = value;
    }

    /**
     * Gets the value of the sihtotstarbed property.
     * 
     * @return
     *     possible object is
     *     {@link ArrayOfSihtotstarve }
     *     
     */
    public ArrayOfSihtotstarve getSihtotstarbed() {
        return sihtotstarbed;
    }

    /**
     * Sets the value of the sihtotstarbed property.
     * 
     * @param value
     *     allowed object is
     *     {@link ArrayOfSihtotstarve }
     *     
     */
    public void setSihtotstarbed(ArrayOfSihtotstarve value) {
        this.sihtotstarbed = value;
    }

    /**
     * Gets the value of the katastriyksuseAadressObjektid property.
     * 
     * @return
     *     possible object is
     *     {@link ArrayOfAadressObjekt }
     *     
     */
    public ArrayOfAadressObjekt getKatastriyksuseAadressObjektid() {
        return katastriyksuseAadressObjektid;
    }

    /**
     * Sets the value of the katastriyksuseAadressObjektid property.
     * 
     * @param value
     *     allowed object is
     *     {@link ArrayOfAadressObjekt }
     *     
     */
    public void setKatastriyksuseAadressObjektid(ArrayOfAadressObjekt value) {
        this.katastriyksuseAadressObjektid = value;
    }

}
