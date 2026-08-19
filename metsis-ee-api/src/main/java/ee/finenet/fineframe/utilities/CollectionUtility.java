package ee.finenet.fineframe.utilities;

import com.google.gson.reflect.TypeToken;

import java.lang.reflect.Type;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import java.util.stream.Collectors;

public class CollectionUtility {

    public static final Type GSON_LIST_OF_STRINGS_TYPE = new TypeToken<List<String>>() {
    }.getType();

    public static <T> List<T> emptyIfNull(List<T> given) {
        return given == null ? Collections.emptyList() : given;
    }

    public static <T> Set<T> emptyIfNull(Set<T> given) {
        return given == null ? Collections.emptySet() : given;
    }

    public static List<String> parseListFromCommaSepparatedString(String given) {
        if (given == null) {
            return Collections.emptyList();
        }
        return Arrays.stream(given.trim().split(",")).filter(Objects::nonNull).collect(Collectors.toList());
    }

    public static List<String> commaSepparatedStringToList(String given) {
        return given == null ? Collections.emptyList() : Arrays.asList(given.split(","));
    }

    @SuppressWarnings("unchecked")
    public static boolean equalLists(List<? extends Comparable> one, List<? extends Comparable> two){
        if (one == null && two == null){
            return true;
        }

        if(one == null || two == null || one.size() != two.size()){
            return false;
        }

        one = new ArrayList<>(one);
        two = new ArrayList<>(two);

        Collections.sort(one);
        Collections.sort(two);
        return one.equals(two);
    }
}
