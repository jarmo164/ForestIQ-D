package ee.metsis.owners;

public class R {
    private final String ownerId;
    private final String ownerName;
    private final String cadastre;

    public R(String ownerId, String ownerName, String cadastre) {
        this.ownerId = ownerId;
        this.ownerName = ownerName;
        this.cadastre = cadastre;
    }

    public String getOwnerId() {
        return ownerId;
    }

    public String getOwnerName() {
        return ownerName;
    }

    public String getCadastre() {
        return cadastre;
    }
}
