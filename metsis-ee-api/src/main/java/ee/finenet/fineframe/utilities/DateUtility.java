package ee.finenet.fineframe.utilities;

import java.text.SimpleDateFormat;
import java.time.Instant;
import java.time.OffsetDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Calendar;
import java.util.Date;

import static java.util.Calendar.APRIL;
import static java.util.Calendar.AUGUST;
import static java.util.Calendar.DECEMBER;
import static java.util.Calendar.FEBRUARY;
import static java.util.Calendar.JANUARY;
import static java.util.Calendar.JULY;
import static java.util.Calendar.JUNE;
import static java.util.Calendar.MARCH;
import static java.util.Calendar.MAY;
import static java.util.Calendar.NOVEMBER;
import static java.util.Calendar.OCTOBER;
import static java.util.Calendar.SEPTEMBER;

public class DateUtility {

    private static final SimpleDateFormat SIMPLE_DATE_FORMAT = new SimpleDateFormat("dd.MM.yyyy");

    public static Date parseUTCISO8601(String input) {
        if (input == null) {
            return null;
        }
        return Date.from(Instant.from(OffsetDateTime.parse(input, DateTimeFormatter.ISO_DATE_TIME)));
    }

    public static String estonianDate(Date d) {
        Calendar cal = Calendar.getInstance();
        cal.setTime(d);
        int month = cal.get(Calendar.MONTH);
        String monthNameInEstonian;
        switch (month) {
            case JANUARY:
                monthNameInEstonian = "jaanuar";
                break;
            case FEBRUARY:
                monthNameInEstonian = "veebruar";
                break;
            case MARCH:
                monthNameInEstonian = "märts";
                break;
            case APRIL:
                monthNameInEstonian = "aprill";
                break;
            case MAY:
                monthNameInEstonian = "mai";
                break;
            case JUNE:
                monthNameInEstonian = "juuni";
                break;
            case JULY:
                monthNameInEstonian = "juuli";
                break;
            case AUGUST:
                monthNameInEstonian = "august";
                break;
            case SEPTEMBER:
                monthNameInEstonian = "september";
                break;
            case OCTOBER:
                monthNameInEstonian = "oktoober";
                break;
            case NOVEMBER:
                monthNameInEstonian = "november";
                break;
            case DECEMBER:
                monthNameInEstonian = "detsember";
                break;
            default:
                throw new IllegalStateException("Unknown month " + month);
        }
        int day = cal.get(Calendar.DAY_OF_MONTH);
        int year = cal.get(Calendar.YEAR);
        return String.format("%s %s %s", day, monthNameInEstonian, year);
    }

    public static String formatSimpleDate(Date d) {
        if (d == null) return null;
        return SIMPLE_DATE_FORMAT.format(d);
    }
}
