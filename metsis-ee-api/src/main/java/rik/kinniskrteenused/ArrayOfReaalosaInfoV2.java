
package rik.kinniskrteenused;

import java.util.ArrayList;
import java.util.List;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlType;


/**
 * <p>Java class for ArrayOfReaalosa_infoV2 complex type.
 * 
 * <p>The following schema fragment specifies the expected content contained within this class.
 * 
 * <pre>
 * &lt;complexType name="ArrayOfReaalosa_infoV2">
 *   &lt;complexContent>
 *     &lt;restriction base="{http://www.w3.org/2001/XMLSchema}anyType">
 *       &lt;sequence>
 *         &lt;element name="Reaalosa_infoV2" type="{http://kinnistusraamat.rik.ee/krteenused/}Reaalosa_infoV2" maxOccurs="unbounded" minOccurs="0"/>
 *       &lt;/sequence>
 *     &lt;/restriction>
 *   &lt;/complexContent>
 * &lt;/complexType>
 * </pre>
 * 
 * 
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "ArrayOfReaalosa_infoV2", propOrder = {
    "reaalosaInfoV2"
})
public class ArrayOfReaalosaInfoV2 {

    @XmlElement(name = "Reaalosa_infoV2", nillable = true)
    protected List<ReaalosaInfoV2> reaalosaInfoV2;

    /**
     * Gets the value of the reaalosaInfoV2 property.
     * 
     * <p>
     * This accessor method returns a reference to the live list,
     * not a snapshot. Therefore any modification you make to the
     * returned list will be present inside the JAXB object.
     * This is why there is not a <CODE>set</CODE> method for the reaalosaInfoV2 property.
     * 
     * <p>
     * For example, to add a new item, do as follows:
     * <pre>
     *    getReaalosaInfoV2().add(newItem);
     * </pre>
     * 
     * 
     * <p>
     * Objects of the following type(s) are allowed in the list
     * {@link ReaalosaInfoV2 }
     * 
     * 
     */
    public List<ReaalosaInfoV2> getReaalosaInfoV2() {
        if (reaalosaInfoV2 == null) {
            reaalosaInfoV2 = new ArrayList<ReaalosaInfoV2>();
        }
        return this.reaalosaInfoV2;
    }

}
