package ee.metsis.contracts;

public class ContactInformation {
    private String email;
    private String phoneNo;
    private String address;

    public String getEmail() {
        return (email == null || email.trim().isEmpty()) ? null : email.trim();
    }

    public void setEmail(String email) {
        this.email = email;
    }

    public String getPhoneNo() {
        return (phoneNo == null || phoneNo.trim().isEmpty()) ? null : phoneNo.trim();
    }

    public void setPhoneNo(String phoneNo) {
        this.phoneNo = phoneNo;
    }

    public String getAddress() {
        return (address == null || address.trim().isEmpty()) ? null : address.trim();
    }

    public void setAddress(String address) {
        this.address = address;
    }
}
