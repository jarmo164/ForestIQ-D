
package rik.kinniskrteenused;

import java.util.ArrayList;
import java.util.List;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlType;


/**
 * <p>Java class for ArrayOfOmandV3 complex type.
 * 
 * <p>The following schema fragment specifies the expected content contained within this class.
 * 
 * <pre>
 * &lt;complexType name="ArrayOfOmandV3">
 *   &lt;complexContent>
 *     &lt;restriction base="{http://www.w3.org/2001/XMLSchema}anyType">
 *       &lt;sequence>
 *         &lt;element name="OmandV3" type="{http://kinnistusraamat.rik.ee/krteenused/}OmandV3" maxOccurs="unbounded" minOccurs="0"/>
 *       &lt;/sequence>
 *     &lt;/restriction>
 *   &lt;/complexContent>
 * &lt;/complexType>
 * </pre>
 * 
 * 
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "ArrayOfOmandV3", propOrder = {
    "omandV3"
})
public class ArrayOfOmandV3 {

    @XmlElement(name = "OmandV3", nillable = true)
    protected List<OmandV3> omandV3;

    /**
     * Gets the value of the omandV3 property.
     * 
     * <p>
     * This accessor method returns a reference to the live list,
     * not a snapshot. Therefore any modification you make to the
     * returned list will be present inside the JAXB object.
     * This is why there is not a <CODE>set</CODE> method for the omandV3 property.
     * 
     * <p>
     * For example, to add a new item, do as follows:
     * <pre>
     *    getOmandV3().add(newItem);
     * </pre>
     * 
     * 
     * <p>
     * Objects of the following type(s) are allowed in the list
     * {@link OmandV3 }
     * 
     * 
     */
    public List<OmandV3> getOmandV3() {
        if (omandV3 == null) {
            omandV3 = new ArrayList<OmandV3>();
        }
        return this.omandV3;
    }

}
