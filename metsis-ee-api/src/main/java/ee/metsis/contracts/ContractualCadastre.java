package ee.metsis.contracts;

import java.util.Comparator;
import java.util.List;

public class ContractualCadastre {
     private String id;
     private String name;
     private String address;
     private String registrationPartNumber;
     private List<ForestSection> forestSections;

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getAddress() {
        return address;
    }

    public void setAddress(String address) {
        this.address = address;
    }

    public List<ForestSection> getForestSections() {
        return forestSections;
    }

    public void setForestSections(List<ForestSection> forestSections) {
        forestSections.sort(Comparator.comparing(ForestSection::getSectionNumber));
        this.forestSections = forestSections;
    }

    public String getRegistrationPartNumber() {
        return registrationPartNumber;
    }

    public void setRegistrationPartNumber(String registrationPartNumber) {
        this.registrationPartNumber = registrationPartNumber;
    }
}
