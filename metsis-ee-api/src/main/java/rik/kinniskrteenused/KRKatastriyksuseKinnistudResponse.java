
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
 *         &lt;element name="KR_katastriyksuse_kinnistudResult" type="{http://kinnistusraamat.rik.ee/krteenused/}KR_Isiku_kinnistud" minOccurs="0"/>
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
    "krKatastriyksuseKinnistudResult"
})
@XmlRootElement(name = "KR_katastriyksuse_kinnistudResponse")
public class KRKatastriyksuseKinnistudResponse {

    @XmlElement(name = "KR_katastriyksuse_kinnistudResult")
    protected KRIsikuKinnistud krKatastriyksuseKinnistudResult;

    /**
     * Gets the value of the krKatastriyksuseKinnistudResult property.
     * 
     * @return
     *     possible object is
     *     {@link KRIsikuKinnistud }
     *     
     */
    public KRIsikuKinnistud getKRKatastriyksuseKinnistudResult() {
        return krKatastriyksuseKinnistudResult;
    }

    /**
     * Sets the value of the krKatastriyksuseKinnistudResult property.
     * 
     * @param value
     *     allowed object is
     *     {@link KRIsikuKinnistud }
     *     
     */
    public void setKRKatastriyksuseKinnistudResult(KRIsikuKinnistud value) {
        this.krKatastriyksuseKinnistudResult = value;
    }

}
