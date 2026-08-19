
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
 *         &lt;element name="KR_katastriyksuse_kinnistud_v2Result" type="{http://kinnistusraamat.rik.ee/krteenused/}KR_Isiku_kinnistudV2" minOccurs="0"/>
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
    "krKatastriyksuseKinnistudV2Result"
})
@XmlRootElement(name = "KR_katastriyksuse_kinnistud_v2Response")
public class KRKatastriyksuseKinnistudV2Response {

    @XmlElement(name = "KR_katastriyksuse_kinnistud_v2Result")
    protected KRIsikuKinnistudV2 krKatastriyksuseKinnistudV2Result;

    /**
     * Gets the value of the krKatastriyksuseKinnistudV2Result property.
     * 
     * @return
     *     possible object is
     *     {@link KRIsikuKinnistudV2 }
     *     
     */
    public KRIsikuKinnistudV2 getKRKatastriyksuseKinnistudV2Result() {
        return krKatastriyksuseKinnistudV2Result;
    }

    /**
     * Sets the value of the krKatastriyksuseKinnistudV2Result property.
     * 
     * @param value
     *     allowed object is
     *     {@link KRIsikuKinnistudV2 }
     *     
     */
    public void setKRKatastriyksuseKinnistudV2Result(KRIsikuKinnistudV2 value) {
        this.krKatastriyksuseKinnistudV2Result = value;
    }

}
