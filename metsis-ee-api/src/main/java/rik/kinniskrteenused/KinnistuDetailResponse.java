
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
 *         &lt;element name="kinnistu_detailResult" type="{http://kinnistusraamat.rik.ee/krteenused/}Kinnistu_detail" minOccurs="0"/>
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
    "kinnistuDetailResult"
})
@XmlRootElement(name = "kinnistu_detailResponse")
public class KinnistuDetailResponse {

    @XmlElement(name = "kinnistu_detailResult")
    protected KinnistuDetail kinnistuDetailResult;

    /**
     * Gets the value of the kinnistuDetailResult property.
     * 
     * @return
     *     possible object is
     *     {@link KinnistuDetail }
     *     
     */
    public KinnistuDetail getKinnistuDetailResult() {
        return kinnistuDetailResult;
    }

    /**
     * Sets the value of the kinnistuDetailResult property.
     * 
     * @param value
     *     allowed object is
     *     {@link KinnistuDetail }
     *     
     */
    public void setKinnistuDetailResult(KinnistuDetail value) {
        this.kinnistuDetailResult = value;
    }

}
