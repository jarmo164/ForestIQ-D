
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
 *         &lt;element name="objektide_arvResult" type="{http://kinnistusraamat.rik.ee/krteenused/}Objektide_arv" minOccurs="0"/>
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
    "objektideArvResult"
})
@XmlRootElement(name = "objektide_arvResponse")
public class ObjektideArvResponse {

    @XmlElement(name = "objektide_arvResult")
    protected ObjektideArv objektideArvResult;

    /**
     * Gets the value of the objektideArvResult property.
     * 
     * @return
     *     possible object is
     *     {@link ObjektideArv }
     *     
     */
    public ObjektideArv getObjektideArvResult() {
        return objektideArvResult;
    }

    /**
     * Sets the value of the objektideArvResult property.
     * 
     * @param value
     *     allowed object is
     *     {@link ObjektideArv }
     *     
     */
    public void setObjektideArvResult(ObjektideArv value) {
        this.objektideArvResult = value;
    }

}
