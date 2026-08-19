package ee.metsis.personsdump;

import spark.Request;

import java.util.Optional;

import static ee.finenet.fineframe.utilities.StringUtility.trimToNull;

public class PersonsDumpCriteria {

    private final String source;
    private final String name;
    private final String phone;
    private final String address;
    private final String code;

    public PersonsDumpCriteria(Request req) {
        this.source = trimToNull(req.queryParams("source"));
        this.name = trimToNull(req.queryParams("name"));
        this.phone = trimToNull(req.queryParams("phone"));
        this.address = trimToNull(req.queryParams("address"));
        this.code = trimToNull(req.queryParams("code"));
    }

    public Optional<String> getSource() {
        return Optional.ofNullable(source);
    }

    public Optional<String> getName() {
        return Optional.ofNullable(name);
    }

    public Optional<String> getPhone() {
        return Optional.ofNullable(phone);
    }

    public Optional<String> getAddress() {
        return Optional.ofNullable(address);
    }

    public Optional<String> getCode() {
        return Optional.ofNullable(code);
    }

}
