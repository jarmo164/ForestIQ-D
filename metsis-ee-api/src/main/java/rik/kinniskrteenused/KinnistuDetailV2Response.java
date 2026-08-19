
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
 *         &lt;element name="kinnistu_detail_v2Result" type="{http://kinnistusraamat.rik.ee/krteenused/}Kinnistu_detailV2" minOccurs="0"/>
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
    "kinnistuDetailV2Result"
})
@XmlRootElement(name = "kinnistu_detail_v2Response")
public class KinnistuDetailV2Response {

    @XmlElement(name = "kinnistu_detail_v2Result")
    protected KinnistuDetailV22 kinnistuDetailV2Result;

    /**
     * Gets the value of the kinnistuDetailV2Result property.
     * 
     * @return
     *     possible object is
     *     {@link KinnistuDetailV22 }
     *     
     */
    public KinnistuDetailV22 getKinnistuDetailV2Result() {
        return kinnistuDetailV2Result;
    }

    /**
     * Sets the value of the kinnistuDetailV2Result property.
     * 
     * @param value
     *     allowed object is
     *     {@link KinnistuDetailV22 }
     *     
     */
    public void setKinnistuDetailV2Result(KinnistuDetailV22 value) {
        this.kinnistuDetailV2Result = value;
    }

}
