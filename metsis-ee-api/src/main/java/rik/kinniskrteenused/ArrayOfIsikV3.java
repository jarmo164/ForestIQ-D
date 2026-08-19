
package rik.kinniskrteenused;

import java.util.ArrayList;
import java.util.List;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlType;


/**
 * <p>Java class for ArrayOfIsikV3 complex type.
 * 
 * <p>The following schema fragment specifies the expected content contained within this class.
 * 
 * <pre>
 * &lt;complexType name="ArrayOfIsikV3">
 *   &lt;complexContent>
 *     &lt;restriction base="{http://www.w3.org/2001/XMLSchema}anyType">
 *       &lt;sequence>
 *         &lt;element name="IsikV3" type="{http://kinnistusraamat.rik.ee/krteenused/}IsikV3" maxOccurs="unbounded" minOccurs="0"/>
 *       &lt;/sequence>
 *     &lt;/restriction>
 *   &lt;/complexContent>
 * &lt;/complexType>
 * </pre>
 * 
 * 
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "ArrayOfIsikV3", propOrder = {
    "isikV3"
})
public class ArrayOfIsikV3 {

    @XmlElement(name = "IsikV3", nillable = true)
    protected List<IsikV3> isikV3;

    /**
     * Gets the value of the isikV3 property.
     * 
     * <p>
     * This accessor method returns a reference to the live list,
     * not a snapshot. Therefore any modification you make to the
     * returned list will be present inside the JAXB object.
     * This is why there is not a <CODE>set</CODE> method for the isikV3 property.
     * 
     * <p>
     * For example, to add a new item, do as follows:
     * <pre>
     *    getIsikV3().add(newItem);
     * </pre>
     * 
     * 
     * <p>
     * Objects of the following type(s) are allowed in the list
     * {@link IsikV3 }
     * 
     * 
     */
    public List<IsikV3> getIsikV3() {
        if (isikV3 == null) {
            isikV3 = new ArrayList<IsikV3>();
        }
        return this.isikV3;
    }

}
