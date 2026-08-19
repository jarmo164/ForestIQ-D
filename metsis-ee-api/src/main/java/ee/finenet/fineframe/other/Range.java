package ee.finenet.fineframe.other;

import java.util.Optional;

public class Range<T> {

    private final T min;
    private final T max;

    public Range(T min, T max) {
        this.min = min;
        this.max = max;
    }

    public Optional<T> getMin() {
        return Optional.ofNullable(min);
    }

    public Optional<T> getMax() {
        return Optional.ofNullable(max);
    }
}
