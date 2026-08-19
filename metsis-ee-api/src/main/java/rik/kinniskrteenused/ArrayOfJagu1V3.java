
package rik.kinniskrteenused;

import java.util.ArrayList;
import java.util.List;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlType;


/**
 * <p>Java class for ArrayOfJagu_1V3 complex type.
 * 
 * <p>The following schema fragment specifies the expected content contained within this class.
 * 
 * <pre>
 * &lt;complexType name="ArrayOfJagu_1V3">
 *   &lt;complexContent>
 *     &lt;restriction base="{http://www.w3.org/2001/XMLSchema}anyType">
 *       &lt;sequence>
 *         &lt;element name="Jagu_1V3" type="{http://kinnistusraamat.rik.ee/krteenused/}Jagu_1V3" maxOccurs="unbounded" minOccurs="0"/>
 *       &lt;/sequence>
 *     &lt;/restriction>
 *   &lt;/complexContent>
 * &lt;/complexType>
 * </pre>
 * 
 * 
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "ArrayOfJagu_1V3", propOrder = {
    "jagu1V3"
})
public class ArrayOfJagu1V3 {

    @XmlElement(name = "Jagu_1V3", nillable = true)
    protected List<Jagu1V3> jagu1V3;

    /**
     * Gets the value of the jagu1V3 property.
     * 
     * <p>
     * This accessor method returns a reference to the live list,
     * not a snapshot. Therefore any modification you make to the
     * returned list will be present inside the JAXB object.
     * This is why there is not a <CODE>set</CODE> method for the jagu1V3 property.
     * 
     * <p>
     * For example, to add a new item, do as follows:
     * <pre>
     *    getJagu1V3().add(newItem);
     * </pre>
     * 
     * 
     * <p>
     * Objects of the following type(s) are allowed in the list
     * {@link Jagu1V3 }
     * 
     * 
     */
    public List<Jagu1V3> getJagu1V3() {
        if (jagu1V3 == null) {
            jagu1V3 = new ArrayList<Jagu1V3>();
        }
        return this.jagu1V3;
    }

}
