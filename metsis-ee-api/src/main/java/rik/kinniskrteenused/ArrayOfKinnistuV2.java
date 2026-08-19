
package rik.kinniskrteenused;

import java.util.ArrayList;
import java.util.List;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlType;


/**
 * <p>Java class for ArrayOfKinnistuV2 complex type.
 * 
 * <p>The following schema fragment specifies the expected content contained within this class.
 * 
 * <pre>
 * &lt;complexType name="ArrayOfKinnistuV2">
 *   &lt;complexContent>
 *     &lt;restriction base="{http://www.w3.org/2001/XMLSchema}anyType">
 *       &lt;sequence>
 *         &lt;element name="KinnistuV2" type="{http://kinnistusraamat.rik.ee/krteenused/}KinnistuV2" maxOccurs="unbounded" minOccurs="0"/>
 *       &lt;/sequence>
 *     &lt;/restriction>
 *   &lt;/complexContent>
 * &lt;/complexType>
 * </pre>
 * 
 * 
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "ArrayOfKinnistuV2", propOrder = {
    "kinnistuV2"
})
public class ArrayOfKinnistuV2 {

    @XmlElement(name = "KinnistuV2", nillable = true)
    protected List<KinnistuV2> kinnistuV2;

    /**
     * Gets the value of the kinnistuV2 property.
     * 
     * <p>
     * This accessor method returns a reference to the live list,
     * not a snapshot. Therefore any modification you make to the
     * returned list will be present inside the JAXB object.
     * This is why there is not a <CODE>set</CODE> method for the kinnistuV2 property.
     * 
     * <p>
     * For example, to add a new item, do as follows:
     * <pre>
     *    getKinnistuV2().add(newItem);
     * </pre>
     * 
     * 
     * <p>
     * Objects of the following type(s) are allowed in the list
     * {@link KinnistuV2 }
     * 
     * 
     */
    public List<KinnistuV2> getKinnistuV2() {
        if (kinnistuV2 == null) {
            kinnistuV2 = new ArrayList<KinnistuV2>();
        }
        return this.kinnistuV2;
    }

}
