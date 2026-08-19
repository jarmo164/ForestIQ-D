package ee.finenet.fineframe.utilities;

public class BooleanUtility {
    public static boolean parseBooleanSilent(String given) {
        try {
            return Boolean.parseBoolean(given);
        } catch (Exception e) {
            return false;
        }
    }
}
