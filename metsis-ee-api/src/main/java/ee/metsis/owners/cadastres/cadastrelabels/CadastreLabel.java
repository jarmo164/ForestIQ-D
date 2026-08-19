package ee.metsis.owners.cadastres.cadastrelabels;

public enum CadastreLabel {
    CONSERVATION_AREA,
    DEAD_LAND,
    SWAMP,
    REAL_ESTATE,
    NOTIFICATIONS_CONSUMED;

    public static CadastreLabel fromString(String id) {
        try {
            return CadastreLabel.valueOf(id);
        } catch (Exception e) {
            return null;
        }
    }
}
