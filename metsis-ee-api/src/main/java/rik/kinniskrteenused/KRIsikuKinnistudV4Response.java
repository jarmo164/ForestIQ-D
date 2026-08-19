
package rik.kinniskrteenused;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
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
 *         &lt;element name="kR_isiku_kinnistud_v4Result" type="{http://kinnistusraamat.rik.ee/krteenused/}KR_Isiku_kinnistudV4" minOccurs="0"/>
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
    "krIsikuKinnistudV4Result"
})
@XmlRootElement(name = "kR_isiku_kinnistud_v4Response")
public class KRIsikuKinnistudV4Response {

    @XmlElement(name = "kR_isiku_kinnistud_v4Result")
    protected KRIsikuKinnistudV4 krIsikuKinnistudV4Result;

    /**
     * Gets the value of the krIsikuKinnistudV4Result property.
     * 
     * @return
     *     possible object is
     *     {@link KRIsikuKinnistudV4 }
     *     
     */
    public KRIsikuKinnistudV4 getKRIsikuKinnistudV4Result() {
        return krIsikuKinnistudV4Result;
    }

    /**
     * Sets the value of the krIsikuKinnistudV4Result property.
     * 
     * @param value
     *     allowed object is
     *     {@link KRIsikuKinnistudV4 }
     *     
     */
    public void setKRIsikuKinnistudV4Result(KRIsikuKinnistudV4 value) {
        this.krIsikuKinnistudV4Result = value;
    }

}
