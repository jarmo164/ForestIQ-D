
package rik.kinniskrteenused;

import java.util.ArrayList;
import java.util.List;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlType;


/**
 * <p>Java class for ArrayOfAvaldus complex type.
 * 
 * <p>The following schema fragment specifies the expected content contained within this class.
 * 
 * <pre>
 * &lt;complexType name="ArrayOfAvaldus">
 *   &lt;complexContent>
 *     &lt;restriction base="{http://www.w3.org/2001/XMLSchema}anyType">
 *       &lt;sequence>
 *         &lt;element name="Avaldus" type="{http://kinnistusraamat.rik.ee/krteenused/}Avaldus" maxOccurs="unbounded" minOccurs="0"/>
 *       &lt;/sequence>
 *     &lt;/restriction>
 *   &lt;/complexContent>
 * &lt;/complexType>
 * </pre>
 * 
 * 
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "ArrayOfAvaldus", propOrder = {
    "avaldus"
})
public class ArrayOfAvaldus {

    @XmlElement(name = "Avaldus", nillable = true)
    protected List<Avaldus> avaldus;

    /**
     * Gets the value of the avaldus property.
     * 
     * <p>
     * This accessor method returns a reference to the live list,
     * not a snapshot. Therefore any modification you make to the
     * returned list will be present inside the JAXB object.
     * This is why there is not a <CODE>set</CODE> method for the avaldus property.
     * 
     * <p>
     * For example, to add a new item, do as follows:
     * <pre>
     *    getAvaldus().add(newItem);
     * </pre>
     * 
     * 
     * <p>
     * Objects of the following type(s) are allowed in the list
     * {@link Avaldus }
     * 
     * 
     */
    public List<Avaldus> getAvaldus() {
        if (avaldus == null) {
            avaldus = new ArrayList<Avaldus>();
        }
        return this.avaldus;
    }

}
