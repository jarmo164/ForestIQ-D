
package rik.kinniskrteenused;

import java.util.ArrayList;
import java.util.List;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlType;


/**
 * <p>Java class for ArrayOfKatastriyksus complex type.
 * 
 * <p>The following schema fragment specifies the expected content contained within this class.
 * 
 * <pre>
 * &lt;complexType name="ArrayOfKatastriyksus">
 *   &lt;complexContent>
 *     &lt;restriction base="{http://www.w3.org/2001/XMLSchema}anyType">
 *       &lt;sequence>
 *         &lt;element name="Katastriyksus" type="{http://kinnistusraamat.rik.ee/krteenused/}Katastriyksus" maxOccurs="unbounded" minOccurs="0"/>
 *       &lt;/sequence>
 *     &lt;/restriction>
 *   &lt;/complexContent>
 * &lt;/complexType>
 * </pre>
 * 
 * 
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "ArrayOfKatastriyksus", propOrder = {
    "katastriyksus"
})
public class ArrayOfKatastriyksus {

    @XmlElement(name = "Katastriyksus", nillable = true)
    protected List<Katastriyksus> katastriyksus;

    /**
     * Gets the value of the katastriyksus property.
     * 
     * <p>
     * This accessor method returns a reference to the live list,
     * not a snapshot. Therefore any modification you make to the
     * returned list will be present inside the JAXB object.
     * This is why there is not a <CODE>set</CODE> method for the katastriyksus property.
     * 
     * <p>
     * For example, to add a new item, do as follows:
     * <pre>
     *    getKatastriyksus().add(newItem);
     * </pre>
     * 
     * 
     * <p>
     * Objects of the following type(s) are allowed in the list
     * {@link Katastriyksus }
     * 
     * 
     */
    public List<Katastriyksus> getKatastriyksus() {
        if (katastriyksus == null) {
            katastriyksus = new ArrayList<Katastriyksus>();
        }
        return this.katastriyksus;
    }

}
