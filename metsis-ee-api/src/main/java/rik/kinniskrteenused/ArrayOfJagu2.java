
package rik.kinniskrteenused;

import java.util.ArrayList;
import java.util.List;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlType;


/**
 * <p>Java class for ArrayOfJagu_2 complex type.
 * 
 * <p>The following schema fragment specifies the expected content contained within this class.
 * 
 * <pre>
 * &lt;complexType name="ArrayOfJagu_2">
 *   &lt;complexContent>
 *     &lt;restriction base="{http://www.w3.org/2001/XMLSchema}anyType">
 *       &lt;sequence>
 *         &lt;element name="Jagu_2" type="{http://kinnistusraamat.rik.ee/krteenused/}Jagu_2" maxOccurs="unbounded" minOccurs="0"/>
 *       &lt;/sequence>
 *     &lt;/restriction>
 *   &lt;/complexContent>
 * &lt;/complexType>
 * </pre>
 * 
 * 
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "ArrayOfJagu_2", propOrder = {
    "jagu2"
})
public class ArrayOfJagu2 {

    @XmlElement(name = "Jagu_2", nillable = true)
    protected List<Jagu2> jagu2;

    /**
     * Gets the value of the jagu2 property.
     * 
     * <p>
     * This accessor method returns a reference to the live list,
     * not a snapshot. Therefore any modification you make to the
     * returned list will be present inside the JAXB object.
     * This is why there is not a <CODE>set</CODE> method for the jagu2 property.
     * 
     * <p>
     * For example, to add a new item, do as follows:
     * <pre>
     *    getJagu2().add(newItem);
     * </pre>
     * 
     * 
     * <p>
     * Objects of the following type(s) are allowed in the list
     * {@link Jagu2 }
     * 
     * 
     */
    public List<Jagu2> getJagu2() {
        if (jagu2 == null) {
            jagu2 = new ArrayList<Jagu2>();
        }
        return this.jagu2;
    }

}
