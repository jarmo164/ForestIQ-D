package ee.finenet.fineframe.utilities;

public class NumbersUtility {
    public static Long parseLongSilent(String given) {
        try {
            return Long.parseLong(given);
        } catch (Exception e) {
            return null;
        }
    }

    public static Integer parseIntSilent(String given) {
        try {
            return Integer.parseInt(given);
        } catch (Exception e) {
            return null;
        }
    }

    public static Double parseDoubleSilent(String given) {
        try {
            return Double.parseDouble(given);
        } catch (Exception e) {
            return null;
        }
    }

    public static boolean isNegative(Double given) {
        return given != null && given < 0;
    }
}
