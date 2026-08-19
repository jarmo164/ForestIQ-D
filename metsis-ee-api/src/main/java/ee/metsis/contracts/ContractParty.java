package ee.metsis.contracts;

public abstract class ContractParty {

    private String name;
    private String code;
    private ContactInformation contactInformation;
    private ContractPartyProxy proxy;

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getCode() {
        return code;
    }

    public void setCode(String code) {
        this.code = code;
    }

    public ContactInformation getContactInformation() {
        return contactInformation;
    }

    public void setContactInformation(ContactInformation contactInformation) {
        this.contactInformation = contactInformation;
    }

    public boolean seemsPrivatePerson() {
        return code.length() == 11;
    }

    public ContractPartyProxy getProxy() {
        return proxy;
    }

    public void setProxy(ContractPartyProxy proxy) {
        this.proxy = proxy;
    }

    public boolean hasProxy() {
        return proxy != null;
    }
}
