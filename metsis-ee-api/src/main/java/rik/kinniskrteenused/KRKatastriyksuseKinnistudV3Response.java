
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
 *         &lt;element name="KR_katastriyksuse_kinnistud_v3Result" type="{http://kinnistusraamat.rik.ee/krteenused/}KR_Isiku_kinnistudV3" minOccurs="0"/>
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
    "krKatastriyksuseKinnistudV3Result"
})
@XmlRootElement(name = "KR_katastriyksuse_kinnistud_v3Response")
public class KRKatastriyksuseKinnistudV3Response {

    @XmlElement(name = "KR_katastriyksuse_kinnistud_v3Result")
    protected KRIsikuKinnistudV3 krKatastriyksuseKinnistudV3Result;

    /**
     * Gets the value of the krKatastriyksuseKinnistudV3Result property.
     * 
     * @return
     *     possible object is
     *     {@link KRIsikuKinnistudV3 }
     *     
     */
    public KRIsikuKinnistudV3 getKRKatastriyksuseKinnistudV3Result() {
        return krKatastriyksuseKinnistudV3Result;
    }

    /**
     * Sets the value of the krKatastriyksuseKinnistudV3Result property.
     * 
     * @param value
     *     allowed object is
     *     {@link KRIsikuKinnistudV3 }
     *     
     */
    public void setKRKatastriyksuseKinnistudV3Result(KRIsikuKinnistudV3 value) {
        this.krKatastriyksuseKinnistudV3Result = value;
    }

}
