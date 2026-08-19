
package rik.kinniskrteenused;

import java.util.ArrayList;
import java.util.List;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlType;


/**
 * <p>Java class for ArrayOfReaalosa_infoV3 complex type.
 * 
 * <p>The following schema fragment specifies the expected content contained within this class.
 * 
 * <pre>
 * &lt;complexType name="ArrayOfReaalosa_infoV3">
 *   &lt;complexContent>
 *     &lt;restriction base="{http://www.w3.org/2001/XMLSchema}anyType">
 *       &lt;sequence>
 *         &lt;element name="Reaalosa_infoV3" type="{http://kinnistusraamat.rik.ee/krteenused/}Reaalosa_infoV3" maxOccurs="unbounded" minOccurs="0"/>
 *       &lt;/sequence>
 *     &lt;/restriction>
 *   &lt;/complexContent>
 * &lt;/complexType>
 * </pre>
 * 
 * 
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "ArrayOfReaalosa_infoV3", propOrder = {
    "reaalosaInfoV3"
})
public class ArrayOfReaalosaInfoV3 {

    @XmlElement(name = "Reaalosa_infoV3", nillable = true)
    protected List<ReaalosaInfoV3> reaalosaInfoV3;

    /**
     * Gets the value of the reaalosaInfoV3 property.
     * 
     * <p>
     * This accessor method returns a reference to the live list,
     * not a snapshot. Therefore any modification you make to the
     * returned list will be present inside the JAXB object.
     * This is why there is not a <CODE>set</CODE> method for the reaalosaInfoV3 property.
     * 
     * <p>
     * For example, to add a new item, do as follows:
     * <pre>
     *    getReaalosaInfoV3().add(newItem);
     * </pre>
     * 
     * 
     * <p>
     * Objects of the following type(s) are allowed in the list
     * {@link ReaalosaInfoV3 }
     * 
     * 
     */
    public List<ReaalosaInfoV3> getReaalosaInfoV3() {
        if (reaalosaInfoV3 == null) {
            reaalosaInfoV3 = new ArrayList<ReaalosaInfoV3>();
        }
        return this.reaalosaInfoV3;
    }

}
