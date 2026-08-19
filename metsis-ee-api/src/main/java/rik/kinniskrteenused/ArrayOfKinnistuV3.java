
package rik.kinniskrteenused;

import java.util.ArrayList;
import java.util.List;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlType;


/**
 * <p>Java class for ArrayOfKinnistuV3 complex type.
 * 
 * <p>The following schema fragment specifies the expected content contained within this class.
 * 
 * <pre>
 * &lt;complexType name="ArrayOfKinnistuV3">
 *   &lt;complexContent>
 *     &lt;restriction base="{http://www.w3.org/2001/XMLSchema}anyType">
 *       &lt;sequence>
 *         &lt;element name="KinnistuV3" type="{http://kinnistusraamat.rik.ee/krteenused/}KinnistuV3" maxOccurs="unbounded" minOccurs="0"/>
 *       &lt;/sequence>
 *     &lt;/restriction>
 *   &lt;/complexContent>
 * &lt;/complexType>
 * </pre>
 * 
 * 
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "ArrayOfKinnistuV3", propOrder = {
    "kinnistuV3"
})
public class ArrayOfKinnistuV3 {

    @XmlElement(name = "KinnistuV3", nillable = true)
    protected List<KinnistuV3> kinnistuV3;

    /**
     * Gets the value of the kinnistuV3 property.
     * 
     * <p>
     * This accessor method returns a reference to the live list,
     * not a snapshot. Therefore any modification you make to the
     * returned list will be present inside the JAXB object.
     * This is why there is not a <CODE>set</CODE> method for the kinnistuV3 property.
     * 
     * <p>
     * For example, to add a new item, do as follows:
     * <pre>
     *    getKinnistuV3().add(newItem);
     * </pre>
     * 
     * 
     * <p>
     * Objects of the following type(s) are allowed in the list
     * {@link KinnistuV3 }
     * 
     * 
     */
    public List<KinnistuV3> getKinnistuV3() {
        if (kinnistuV3 == null) {
            kinnistuV3 = new ArrayList<KinnistuV3>();
        }
        return this.kinnistuV3;
    }

}
