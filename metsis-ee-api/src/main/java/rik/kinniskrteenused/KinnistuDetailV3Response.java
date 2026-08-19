
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
 *         &lt;element name="kinnistu_detail_v3Result" type="{http://kinnistusraamat.rik.ee/krteenused/}Kinnistu_detailV3" minOccurs="0"/>
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
    "kinnistuDetailV3Result"
})
@XmlRootElement(name = "kinnistu_detail_v3Response")
public class KinnistuDetailV3Response {

    @XmlElement(name = "kinnistu_detail_v3Result")
    protected KinnistuDetailV3 kinnistuDetailV3Result;

    /**
     * Gets the value of the kinnistuDetailV3Result property.
     * 
     * @return
     *     possible object is
     *     {@link KinnistuDetailV3 }
     *     
     */
    public KinnistuDetailV3 getKinnistuDetailV3Result() {
        return kinnistuDetailV3Result;
    }

    /**
     * Sets the value of the kinnistuDetailV3Result property.
     * 
     * @param value
     *     allowed object is
     *     {@link KinnistuDetailV3 }
     *     
     */
    public void setKinnistuDetailV3Result(KinnistuDetailV3 value) {
        this.kinnistuDetailV3Result = value;
    }

}
