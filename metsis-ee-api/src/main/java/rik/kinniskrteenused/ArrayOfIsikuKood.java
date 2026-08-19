
package rik.kinniskrteenused;

import java.util.ArrayList;
import java.util.List;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlType;


/**
 * <p>Java class for ArrayOfIsiku_kood complex type.
 * 
 * <p>The following schema fragment specifies the expected content contained within this class.
 * 
 * <pre>
 * &lt;complexType name="ArrayOfIsiku_kood">
 *   &lt;complexContent>
 *     &lt;restriction base="{http://www.w3.org/2001/XMLSchema}anyType">
 *       &lt;sequence>
 *         &lt;element name="Isiku_kood" type="{http://kinnistusraamat.rik.ee/krteenused/}Isiku_kood" maxOccurs="unbounded" minOccurs="0"/>
 *       &lt;/sequence>
 *     &lt;/restriction>
 *   &lt;/complexContent>
 * &lt;/complexType>
 * </pre>
 * 
 * 
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "ArrayOfIsiku_kood", propOrder = {
    "isikuKood"
})
public class ArrayOfIsikuKood {

    @XmlElement(name = "Isiku_kood", nillable = true)
    protected List<IsikuKood> isikuKood;

    /**
     * Gets the value of the isikuKood property.
     * 
     * <p>
     * This accessor method returns a reference to the live list,
     * not a snapshot. Therefore any modification you make to the
     * returned list will be present inside the JAXB object.
     * This is why there is not a <CODE>set</CODE> method for the isikuKood property.
     * 
     * <p>
     * For example, to add a new item, do as follows:
     * <pre>
     *    getIsikuKood().add(newItem);
     * </pre>
     * 
     * 
     * <p>
     * Objects of the following type(s) are allowed in the list
     * {@link IsikuKood }
     * 
     * 
     */
    public List<IsikuKood> getIsikuKood() {
        if (isikuKood == null) {
            isikuKood = new ArrayList<IsikuKood>();
        }
        return this.isikuKood;
    }

}
