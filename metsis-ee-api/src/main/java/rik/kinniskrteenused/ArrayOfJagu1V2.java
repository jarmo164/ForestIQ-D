
package rik.kinniskrteenused;

import java.util.ArrayList;
import java.util.List;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlType;


/**
 * <p>Java class for ArrayOfJagu_1V2 complex type.
 * 
 * <p>The following schema fragment specifies the expected content contained within this class.
 * 
 * <pre>
 * &lt;complexType name="ArrayOfJagu_1V2">
 *   &lt;complexContent>
 *     &lt;restriction base="{http://www.w3.org/2001/XMLSchema}anyType">
 *       &lt;sequence>
 *         &lt;element name="Jagu_1V2" type="{http://kinnistusraamat.rik.ee/krteenused/}Jagu_1V2" maxOccurs="unbounded" minOccurs="0"/>
 *       &lt;/sequence>
 *     &lt;/restriction>
 *   &lt;/complexContent>
 * &lt;/complexType>
 * </pre>
 * 
 * 
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "ArrayOfJagu_1V2", propOrder = {
    "jagu1V2"
})
public class ArrayOfJagu1V2 {

    @XmlElement(name = "Jagu_1V2", nillable = true)
    protected List<Jagu1V2> jagu1V2;

    /**
     * Gets the value of the jagu1V2 property.
     * 
     * <p>
     * This accessor method returns a reference to the live list,
     * not a snapshot. Therefore any modification you make to the
     * returned list will be present inside the JAXB object.
     * This is why there is not a <CODE>set</CODE> method for the jagu1V2 property.
     * 
     * <p>
     * For example, to add a new item, do as follows:
     * <pre>
     *    getJagu1V2().add(newItem);
     * </pre>
     * 
     * 
     * <p>
     * Objects of the following type(s) are allowed in the list
     * {@link Jagu1V2 }
     * 
     * 
     */
    public List<Jagu1V2> getJagu1V2() {
        if (jagu1V2 == null) {
            jagu1V2 = new ArrayList<Jagu1V2>();
        }
        return this.jagu1V2;
    }

}
