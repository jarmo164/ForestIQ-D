
package rik.kinniskrteenused;

import java.util.ArrayList;
import java.util.List;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlType;


/**
 * <p>Java class for ArrayOfKinnistuV4 complex type.
 * 
 * <p>The following schema fragment specifies the expected content contained within this class.
 * 
 * <pre>
 * &lt;complexType name="ArrayOfKinnistuV4">
 *   &lt;complexContent>
 *     &lt;restriction base="{http://www.w3.org/2001/XMLSchema}anyType">
 *       &lt;sequence>
 *         &lt;element name="KinnistuV4" type="{http://kinnistusraamat.rik.ee/krteenused/}KinnistuV4" maxOccurs="unbounded" minOccurs="0"/>
 *       &lt;/sequence>
 *     &lt;/restriction>
 *   &lt;/complexContent>
 * &lt;/complexType>
 * </pre>
 * 
 * 
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "ArrayOfKinnistuV4", propOrder = {
    "kinnistuV4"
})
public class ArrayOfKinnistuV4 {

    @XmlElement(name = "KinnistuV4", nillable = true)
    protected List<KinnistuV4> kinnistuV4;

    /**
     * Gets the value of the kinnistuV4 property.
     * 
     * <p>
     * This accessor method returns a reference to the live list,
     * not a snapshot. Therefore any modification you make to the
     * returned list will be present inside the JAXB object.
     * This is why there is not a <CODE>set</CODE> method for the kinnistuV4 property.
     * 
     * <p>
     * For example, to add a new item, do as follows:
     * <pre>
     *    getKinnistuV4().add(newItem);
     * </pre>
     * 
     * 
     * <p>
     * Objects of the following type(s) are allowed in the list
     * {@link KinnistuV4 }
     * 
     * 
     */
    public List<KinnistuV4> getKinnistuV4() {
        if (kinnistuV4 == null) {
            kinnistuV4 = new ArrayList<KinnistuV4>();
        }
        return this.kinnistuV4;
    }

}
