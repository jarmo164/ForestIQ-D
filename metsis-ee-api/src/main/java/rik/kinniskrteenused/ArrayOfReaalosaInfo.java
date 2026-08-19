
package rik.kinniskrteenused;

import java.util.ArrayList;
import java.util.List;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlType;


/**
 * <p>Java class for ArrayOfReaalosa_info complex type.
 * 
 * <p>The following schema fragment specifies the expected content contained within this class.
 * 
 * <pre>
 * &lt;complexType name="ArrayOfReaalosa_info">
 *   &lt;complexContent>
 *     &lt;restriction base="{http://www.w3.org/2001/XMLSchema}anyType">
 *       &lt;sequence>
 *         &lt;element name="Reaalosa_info" type="{http://kinnistusraamat.rik.ee/krteenused/}Reaalosa_info" maxOccurs="unbounded" minOccurs="0"/>
 *       &lt;/sequence>
 *     &lt;/restriction>
 *   &lt;/complexContent>
 * &lt;/complexType>
 * </pre>
 * 
 * 
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "ArrayOfReaalosa_info", propOrder = {
    "reaalosaInfo"
})
public class ArrayOfReaalosaInfo {

    @XmlElement(name = "Reaalosa_info", nillable = true)
    protected List<ReaalosaInfo> reaalosaInfo;

    /**
     * Gets the value of the reaalosaInfo property.
     * 
     * <p>
     * This accessor method returns a reference to the live list,
     * not a snapshot. Therefore any modification you make to the
     * returned list will be present inside the JAXB object.
     * This is why there is not a <CODE>set</CODE> method for the reaalosaInfo property.
     * 
     * <p>
     * For example, to add a new item, do as follows:
     * <pre>
     *    getReaalosaInfo().add(newItem);
     * </pre>
     * 
     * 
     * <p>
     * Objects of the following type(s) are allowed in the list
     * {@link ReaalosaInfo }
     * 
     * 
     */
    public List<ReaalosaInfo> getReaalosaInfo() {
        if (reaalosaInfo == null) {
            reaalosaInfo = new ArrayList<ReaalosaInfo>();
        }
        return this.reaalosaInfo;
    }

}
