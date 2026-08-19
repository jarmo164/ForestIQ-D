
package rik.kinniskrteenused;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlType;


/**
 * <p>Java class for Kinnistu_detail complex type.
 * 
 * <p>The following schema fragment specifies the expected content contained within this class.
 * 
 * <pre>
 * &lt;complexType name="Kinnistu_detail">
 *   &lt;complexContent>
 *     &lt;restriction base="{http://www.w3.org/2001/XMLSchema}anyType">
 *       &lt;sequence>
 *         &lt;element name="systeemiteade" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="veateade" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="liik" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="avaldused" type="{http://kinnistusraamat.rik.ee/krteenused/}ArrayOfAvaldus" minOccurs="0"/>
 *         &lt;element name="jaoskond" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="kinnistusosakond" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="teade" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="uus_nr" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="vana_nr" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="nimi" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="oigsuse_marge" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="kandetekstid_genereerimisel" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="digitaalne_toimik" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="digitaalne_kp" type="{http://www.w3.org/2001/XMLSchema}string" minOccurs="0"/>
 *         &lt;element name="jaod_0" type="{http://kinnistusraamat.rik.ee/krteenused/}ArrayOfJagu_0" minOccurs="0"/>
 *         &lt;element name="jaod_1" type="{http://kinnistusraamat.rik.ee/krteenused/}ArrayOfJagu_1" minOccurs="0"/>
 *         &lt;element name="jaod_2" type="{http://kinnistusraamat.rik.ee/krteenused/}ArrayOfJagu_2" minOccurs="0"/>
 *         &lt;element name="jaod_3" type="{http://kinnistusraamat.rik.ee/krteenused/}ArrayOfJagu_3" minOccurs="0"/>
 *         &lt;element name="jaod_4" type="{http://kinnistusraamat.rik.ee/krteenused/}ArrayOfJagu_4" minOccurs="0"/>
 *       &lt;/sequence>
 *     &lt;/restriction>
 *   &lt;/complexContent>
 * &lt;/complexType>
 * </pre>
 * 
 * 
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "Kinnistu_detail", propOrder = {
    "systeemiteade",
    "veateade",
    "liik",
    "avaldused",
    "jaoskond",
    "kinnistusosakond",
    "teade",
    "uusNr",
    "vanaNr",
    "nimi",
    "oigsuseMarge",
    "kandetekstidGenereerimisel",
    "digitaalneToimik",
    "digitaalneKp",
    "jaod0",
    "jaod1",
    "jaod2",
    "jaod3",
    "jaod4"
})
public class KinnistuDetail {

    protected String systeemiteade;
    protected String veateade;
    protected String liik;
    protected ArrayOfAvaldus avaldused;
    protected String jaoskond;
    protected String kinnistusosakond;
    protected String teade;
    @XmlElement(name = "uus_nr")
    protected String uusNr;
    @XmlElement(name = "vana_nr")
    protected String vanaNr;
    protected String nimi;
    @XmlElement(name = "oigsuse_marge")
    protected String oigsuseMarge;
    @XmlElement(name = "kandetekstid_genereerimisel")
    protected String kandetekstidGenereerimisel;
    @XmlElement(name = "digitaalne_toimik")
    protected String digitaalneToimik;
    @XmlElement(name = "digitaalne_kp")
    protected String digitaalneKp;
    @XmlElement(name = "jaod_0")
    protected ArrayOfJagu0 jaod0;
    @XmlElement(name = "jaod_1")
    protected ArrayOfJagu1 jaod1;
    @XmlElement(name = "jaod_2")
    protected ArrayOfJagu2 jaod2;
    @XmlElement(name = "jaod_3")
    protected ArrayOfJagu3 jaod3;
    @XmlElement(name = "jaod_4")
    protected ArrayOfJagu4 jaod4;

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
     * Gets the value of the avaldused property.
     * 
     * @return
     *     possible object is
     *     {@link ArrayOfAvaldus }
     *     
     */
    public ArrayOfAvaldus getAvaldused() {
        return avaldused;
    }

    /**
     * Sets the value of the avaldused property.
     * 
     * @param value
     *     allowed object is
     *     {@link ArrayOfAvaldus }
     *     
     */
    public void setAvaldused(ArrayOfAvaldus value) {
        this.avaldused = value;
    }

    /**
     * Gets the value of the jaoskond property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getJaoskond() {
        return jaoskond;
    }

    /**
     * Sets the value of the jaoskond property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setJaoskond(String value) {
        this.jaoskond = value;
    }

    /**
     * Gets the value of the kinnistusosakond property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getKinnistusosakond() {
        return kinnistusosakond;
    }

    /**
     * Sets the value of the kinnistusosakond property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setKinnistusosakond(String value) {
        this.kinnistusosakond = value;
    }

    /**
     * Gets the value of the teade property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getTeade() {
        return teade;
    }

    /**
     * Sets the value of the teade property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setTeade(String value) {
        this.teade = value;
    }

    /**
     * Gets the value of the uusNr property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getUusNr() {
        return uusNr;
    }

    /**
     * Sets the value of the uusNr property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setUusNr(String value) {
        this.uusNr = value;
    }

    /**
     * Gets the value of the vanaNr property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getVanaNr() {
        return vanaNr;
    }

    /**
     * Sets the value of the vanaNr property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setVanaNr(String value) {
        this.vanaNr = value;
    }

    /**
     * Gets the value of the nimi property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getNimi() {
        return nimi;
    }

    /**
     * Sets the value of the nimi property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setNimi(String value) {
        this.nimi = value;
    }

    /**
     * Gets the value of the oigsuseMarge property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getOigsuseMarge() {
        return oigsuseMarge;
    }

    /**
     * Sets the value of the oigsuseMarge property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setOigsuseMarge(String value) {
        this.oigsuseMarge = value;
    }

    /**
     * Gets the value of the kandetekstidGenereerimisel property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getKandetekstidGenereerimisel() {
        return kandetekstidGenereerimisel;
    }

    /**
     * Sets the value of the kandetekstidGenereerimisel property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setKandetekstidGenereerimisel(String value) {
        this.kandetekstidGenereerimisel = value;
    }

    /**
     * Gets the value of the digitaalneToimik property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getDigitaalneToimik() {
        return digitaalneToimik;
    }

    /**
     * Sets the value of the digitaalneToimik property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setDigitaalneToimik(String value) {
        this.digitaalneToimik = value;
    }

    /**
     * Gets the value of the digitaalneKp property.
     * 
     * @return
     *     possible object is
     *     {@link String }
     *     
     */
    public String getDigitaalneKp() {
        return digitaalneKp;
    }

    /**
     * Sets the value of the digitaalneKp property.
     * 
     * @param value
     *     allowed object is
     *     {@link String }
     *     
     */
    public void setDigitaalneKp(String value) {
        this.digitaalneKp = value;
    }

    /**
     * Gets the value of the jaod0 property.
     * 
     * @return
     *     possible object is
     *     {@link ArrayOfJagu0 }
     *     
     */
    public ArrayOfJagu0 getJaod0() {
        return jaod0;
    }

    /**
     * Sets the value of the jaod0 property.
     * 
     * @param value
     *     allowed object is
     *     {@link ArrayOfJagu0 }
     *     
     */
    public void setJaod0(ArrayOfJagu0 value) {
        this.jaod0 = value;
    }

    /**
     * Gets the value of the jaod1 property.
     * 
     * @return
     *     possible object is
     *     {@link ArrayOfJagu1 }
     *     
     */
    public ArrayOfJagu1 getJaod1() {
        return jaod1;
    }

    /**
     * Sets the value of the jaod1 property.
     * 
     * @param value
     *     allowed object is
     *     {@link ArrayOfJagu1 }
     *     
     */
    public void setJaod1(ArrayOfJagu1 value) {
        this.jaod1 = value;
    }

    /**
     * Gets the value of the jaod2 property.
     * 
     * @return
     *     possible object is
     *     {@link ArrayOfJagu2 }
     *     
     */
    public ArrayOfJagu2 getJaod2() {
        return jaod2;
    }

    /**
     * Sets the value of the jaod2 property.
     * 
     * @param value
     *     allowed object is
     *     {@link ArrayOfJagu2 }
     *     
     */
    public void setJaod2(ArrayOfJagu2 value) {
        this.jaod2 = value;
    }

    /**
     * Gets the value of the jaod3 property.
     * 
     * @return
     *     possible object is
     *     {@link ArrayOfJagu3 }
     *     
     */
    public ArrayOfJagu3 getJaod3() {
        return jaod3;
    }

    /**
     * Sets the value of the jaod3 property.
     * 
     * @param value
     *     allowed object is
     *     {@link ArrayOfJagu3 }
     *     
     */
    public void setJaod3(ArrayOfJagu3 value) {
        this.jaod3 = value;
    }

    /**
     * Gets the value of the jaod4 property.
     * 
     * @return
     *     possible object is
     *     {@link ArrayOfJagu4 }
     *     
     */
    public ArrayOfJagu4 getJaod4() {
        return jaod4;
    }

    /**
     * Sets the value of the jaod4 property.
     * 
     * @param value
     *     allowed object is
     *     {@link ArrayOfJagu4 }
     *     
     */
    public void setJaod4(ArrayOfJagu4 value) {
        this.jaod4 = value;
    }

}
