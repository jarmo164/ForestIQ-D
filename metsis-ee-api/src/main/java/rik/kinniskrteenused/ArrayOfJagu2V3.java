
package rik.kinniskrteenused;

import java.util.ArrayList;
import java.util.List;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlType;


/**
 * <p>Java class for ArrayOfJagu_2V3 complex type.
 * 
 * <p>The following schema fragment specifies the expected content contained within this class.
 * 
 * <pre>
 * &lt;complexType name="ArrayOfJagu_2V3">
 *   &lt;complexContent>
 *     &lt;restriction base="{http://www.w3.org/2001/XMLSchema}anyType">
 *       &lt;sequence>
 *         &lt;element name="Jagu_2V3" type="{http://kinnistusraamat.rik.ee/krteenused/}Jagu_2V3" maxOccurs="unbounded" minOccurs="0"/>
 *       &lt;/sequence>
 *     &lt;/restriction>
 *   &lt;/complexContent>
 * &lt;/complexType>
 * </pre>
 * 
 * 
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "ArrayOfJagu_2V3", propOrder = {
    "jagu2V3"
})
public class ArrayOfJagu2V3 {

    @XmlElement(name = "Jagu_2V3", nillable = true)
    protected List<Jagu2V3> jagu2V3;

    /**
     * Gets the value of the jagu2V3 property.
     * 
     * <p>
     * This accessor method returns a reference to the live list,
     * not a snapshot. Therefore any modification you make to the
     * returned list will be present inside the JAXB object.
     * This is why there is not a <CODE>set</CODE> method for the jagu2V3 property.
     * 
     * <p>
     * For example, to add a new item, do as follows:
     * <pre>
     *    getJagu2V3().add(newItem);
     * </pre>
     * 
     * 
     * <p>
     * Objects of the following type(s) are allowed in the list
     * {@link Jagu2V3 }
     * 
     * 
     */
    public List<Jagu2V3> getJagu2V3() {
        if (jagu2V3 == null) {
            jagu2V3 = new ArrayList<Jagu2V3>();
        }
        return this.jagu2V3;
    }

}
