
package rik.kinniskrteenused;

import java.util.ArrayList;
import java.util.List;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlType;


/**
 * <p>Java class for ArrayOfSihtotstarve complex type.
 * 
 * <p>The following schema fragment specifies the expected content contained within this class.
 * 
 * <pre>
 * &lt;complexType name="ArrayOfSihtotstarve">
 *   &lt;complexContent>
 *     &lt;restriction base="{http://www.w3.org/2001/XMLSchema}anyType">
 *       &lt;sequence>
 *         &lt;element name="Sihtotstarve" type="{http://kinnistusraamat.rik.ee/krteenused/}Sihtotstarve" maxOccurs="unbounded" minOccurs="0"/>
 *       &lt;/sequence>
 *     &lt;/restriction>
 *   &lt;/complexContent>
 * &lt;/complexType>
 * </pre>
 * 
 * 
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "ArrayOfSihtotstarve", propOrder = {
    "sihtotstarve"
})
public class ArrayOfSihtotstarve {

    @XmlElement(name = "Sihtotstarve", nillable = true)
    protected List<Sihtotstarve> sihtotstarve;

    /**
     * Gets the value of the sihtotstarve property.
     * 
     * <p>
     * This accessor method returns a reference to the live list,
     * not a snapshot. Therefore any modification you make to the
     * returned list will be present inside the JAXB object.
     * This is why there is not a <CODE>set</CODE> method for the sihtotstarve property.
     * 
     * <p>
     * For example, to add a new item, do as follows:
     * <pre>
     *    getSihtotstarve().add(newItem);
     * </pre>
     * 
     * 
     * <p>
     * Objects of the following type(s) are allowed in the list
     * {@link Sihtotstarve }
     * 
     * 
     */
    public List<Sihtotstarve> getSihtotstarve() {
        if (sihtotstarve == null) {
            sihtotstarve = new ArrayList<Sihtotstarve>();
        }
        return this.sihtotstarve;
    }

}
