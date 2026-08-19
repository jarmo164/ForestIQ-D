package ee.metsis.personsdump;

public class PersonsDumpEntry {
    private final Long id;
    private final String source;
    private final String name;
    private final String phone;
    private final String address;
    private final String code;

    public PersonsDumpEntry(Long id, String source, String name, String phone, String address, String code) {
        this.id = id;
        this.source = source;
        this.name = name;
        this.phone = phone;
        this.address = address;
        this.code = code;
    }

    public Long getId() {
        return id;
    }

    public String getSource() {
        return source;
    }

    public String getName() {
        return name;
    }

    public String getPhone() {
        return phone;
    }

    public String getAddress() {
        return address;
    }

    public String getCode() {
        return code;
    }
}
