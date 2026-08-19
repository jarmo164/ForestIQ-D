package ee.rik.kinnisturaamat.services;

public class CadastreCountRequest {

    private final String name;
    private final OwnerType type;
    private final String code;

    public CadastreCountRequest(String name, OwnerType type, String code) {
        this.name = name;
        this.type = type;
        this.code = code;
    }

    public String getName() {
        return name;
    }

    public OwnerType getType() {
        return type;
    }

    public String getCode() {
        return code;
    }

    public enum OwnerType {
        ERAISIK, FIRMAD
    }
}
