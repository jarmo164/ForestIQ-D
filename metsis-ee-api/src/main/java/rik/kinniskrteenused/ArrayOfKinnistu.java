
package rik.kinniskrteenused;

import java.util.ArrayList;
import java.util.List;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlType;


/**
 * <p>Java class for ArrayOfKinnistu complex type.
 * 
 * <p>The following schema fragment specifies the expected content contained within this class.
 * 
 * <pre>
 * &lt;complexType name="ArrayOfKinnistu">
 *   &lt;complexContent>
 *     &lt;restriction base="{http://www.w3.org/2001/XMLSchema}anyType">
 *       &lt;sequence>
 *         &lt;element name="Kinnistu" type="{http://kinnistusraamat.rik.ee/krteenused/}Kinnistu" maxOccurs="unbounded" minOccurs="0"/>
 *       &lt;/sequence>
 *     &lt;/restriction>
 *   &lt;/complexContent>
 * &lt;/complexType>
 * </pre>
 * 
 * 
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "ArrayOfKinnistu", propOrder = {
    "kinnistu"
})
public class ArrayOfKinnistu {

    @XmlElement(name = "Kinnistu", nillable = true)
    protected List<Kinnistu> kinnistu;

    /**
     * Gets the value of the kinnistu property.
     * 
     * <p>
     * This accessor method returns a reference to the live list,
     * not a snapshot. Therefore any modification you make to the
     * returned list will be present inside the JAXB object.
     * This is why there is not a <CODE>set</CODE> method for the kinnistu property.
     * 
     * <p>
     * For example, to add a new item, do as follows:
     * <pre>
     *    getKinnistu().add(newItem);
     * </pre>
     * 
     * 
     * <p>
     * Objects of the following type(s) are allowed in the list
     * {@link Kinnistu }
     * 
     * 
     */
    public List<Kinnistu> getKinnistu() {
        if (kinnistu == null) {
            kinnistu = new ArrayList<Kinnistu>();
        }
        return this.kinnistu;
    }

}
