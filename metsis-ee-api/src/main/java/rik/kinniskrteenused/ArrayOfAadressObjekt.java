
package rik.kinniskrteenused;

import java.util.ArrayList;
import java.util.List;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlType;


/**
 * <p>Java class for ArrayOfAadressObjekt complex type.
 * 
 * <p>The following schema fragment specifies the expected content contained within this class.
 * 
 * <pre>
 * &lt;complexType name="ArrayOfAadressObjekt">
 *   &lt;complexContent>
 *     &lt;restriction base="{http://www.w3.org/2001/XMLSchema}anyType">
 *       &lt;sequence>
 *         &lt;element name="AadressObjekt" type="{http://kinnistusraamat.rik.ee/krteenused/}AadressObjekt" maxOccurs="unbounded" minOccurs="0"/>
 *       &lt;/sequence>
 *     &lt;/restriction>
 *   &lt;/complexContent>
 * &lt;/complexType>
 * </pre>
 * 
 * 
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "ArrayOfAadressObjekt", propOrder = {
    "aadressObjekt"
})
public class ArrayOfAadressObjekt {

    @XmlElement(name = "AadressObjekt", nillable = true)
    protected List<AadressObjekt> aadressObjekt;

    /**
     * Gets the value of the aadressObjekt property.
     * 
     * <p>
     * This accessor method returns a reference to the live list,
     * not a snapshot. Therefore any modification you make to the
     * returned list will be present inside the JAXB object.
     * This is why there is not a <CODE>set</CODE> method for the aadressObjekt property.
     * 
     * <p>
     * For example, to add a new item, do as follows:
     * <pre>
     *    getAadressObjekt().add(newItem);
     * </pre>
     * 
     * 
     * <p>
     * Objects of the following type(s) are allowed in the list
     * {@link AadressObjekt }
     * 
     * 
     */
    public List<AadressObjekt> getAadressObjekt() {
        if (aadressObjekt == null) {
            aadressObjekt = new ArrayList<AadressObjekt>();
        }
        return this.aadressObjekt;
    }

}
