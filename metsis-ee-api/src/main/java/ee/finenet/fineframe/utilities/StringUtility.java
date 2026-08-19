package ee.finenet.fineframe.utilities;

public class StringUtility {
    public static String emptyIfNull(String given) {
        return given == null ? "" : given;
    }

    public static String removeSubstring(String original, String removable) {
        return original == null ? null : original.replace(removable, "");
    }

    public static boolean isNullOrBlank(String given) {
        return given == null || given.trim().isEmpty();
    }

    public static String trimToNull(String given) {
        if (given == null) {
            return null;
        }
        given = given.trim();
        return given.isEmpty() ? null : given;
    }

    public static String trimToEmpty(String given) {
        if (given == null) {
            return "";
        }
        return given.trim();
    }

    public static String toString(Object o) {
        return o == null ? null : o.toString();
    }

    public static String enumToString(Enum e) {
        return e == null ? null : e.name();
    }
}
