
package rik.kinniskrteenused;

import java.util.ArrayList;
import java.util.List;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlType;


/**
 * <p>Java class for ArrayOfIsiku_koodV3 complex type.
 * 
 * <p>The following schema fragment specifies the expected content contained within this class.
 * 
 * <pre>
 * &lt;complexType name="ArrayOfIsiku_koodV3">
 *   &lt;complexContent>
 *     &lt;restriction base="{http://www.w3.org/2001/XMLSchema}anyType">
 *       &lt;sequence>
 *         &lt;element name="Isiku_koodV3" type="{http://kinnistusraamat.rik.ee/krteenused/}Isiku_koodV3" maxOccurs="unbounded" minOccurs="0"/>
 *       &lt;/sequence>
 *     &lt;/restriction>
 *   &lt;/complexContent>
 * &lt;/complexType>
 * </pre>
 * 
 * 
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "ArrayOfIsiku_koodV3", propOrder = {
    "isikuKoodV3"
})
public class ArrayOfIsikuKoodV3 {

    @XmlElement(name = "Isiku_koodV3", nillable = true)
    protected List<IsikuKoodV3> isikuKoodV3;

    /**
     * Gets the value of the isikuKoodV3 property.
     * 
     * <p>
     * This accessor method returns a reference to the live list,
     * not a snapshot. Therefore any modification you make to the
     * returned list will be present inside the JAXB object.
     * This is why there is not a <CODE>set</CODE> method for the isikuKoodV3 property.
     * 
     * <p>
     * For example, to add a new item, do as follows:
     * <pre>
     *    getIsikuKoodV3().add(newItem);
     * </pre>
     * 
     * 
     * <p>
     * Objects of the following type(s) are allowed in the list
     * {@link IsikuKoodV3 }
     * 
     * 
     */
    public List<IsikuKoodV3> getIsikuKoodV3() {
        if (isikuKoodV3 == null) {
            isikuKoodV3 = new ArrayList<IsikuKoodV3>();
        }
        return this.isikuKoodV3;
    }

}
