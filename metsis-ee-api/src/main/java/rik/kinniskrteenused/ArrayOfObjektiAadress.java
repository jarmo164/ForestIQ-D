
package rik.kinniskrteenused;

import java.util.ArrayList;
import java.util.List;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlType;


/**
 * <p>Java class for ArrayOfObjektiAadress complex type.
 * 
 * <p>The following schema fragment specifies the expected content contained within this class.
 * 
 * <pre>
 * &lt;complexType name="ArrayOfObjektiAadress">
 *   &lt;complexContent>
 *     &lt;restriction base="{http://www.w3.org/2001/XMLSchema}anyType">
 *       &lt;sequence>
 *         &lt;element name="ObjektiAadress" type="{http://kinnistusraamat.rik.ee/krteenused/}ObjektiAadress" maxOccurs="unbounded" minOccurs="0"/>
 *       &lt;/sequence>
 *     &lt;/restriction>
 *   &lt;/complexContent>
 * &lt;/complexType>
 * </pre>
 * 
 * 
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "ArrayOfObjektiAadress", propOrder = {
    "objektiAadress"
})
public class ArrayOfObjektiAadress {

    @XmlElement(name = "ObjektiAadress", nillable = true)
    protected List<ObjektiAadress> objektiAadress;

    /**
     * Gets the value of the objektiAadress property.
     * 
     * <p>
     * This accessor method returns a reference to the live list,
     * not a snapshot. Therefore any modification you make to the
     * returned list will be present inside the JAXB object.
     * This is why there is not a <CODE>set</CODE> method for the objektiAadress property.
     * 
     * <p>
     * For example, to add a new item, do as follows:
     * <pre>
     *    getObjektiAadress().add(newItem);
     * </pre>
     * 
     * 
     * <p>
     * Objects of the following type(s) are allowed in the list
     * {@link ObjektiAadress }
     * 
     * 
     */
    public List<ObjektiAadress> getObjektiAadress() {
        if (objektiAadress == null) {
            objektiAadress = new ArrayList<ObjektiAadress>();
        }
        return this.objektiAadress;
    }

}
