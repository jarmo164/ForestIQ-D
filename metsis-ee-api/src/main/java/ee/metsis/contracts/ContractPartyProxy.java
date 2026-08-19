package ee.metsis.contracts;

public class ContractPartyProxy {

    private String name;
    private String code;
    private ContactInformation contactInformation;
    private ProxyRepresentationBase proxyRepresentationBase;

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

    public ProxyRepresentationBase getProxyRepresentationBase() {
        return proxyRepresentationBase;
    }

    public void setProxyRepresentationBase(ProxyRepresentationBase proxyRepresentationBase) {
        this.proxyRepresentationBase = proxyRepresentationBase;
    }
}

enum ProxyRepresentationBase {
    MEMBER_OF_BOARD,
    AUTHORISATION
}
