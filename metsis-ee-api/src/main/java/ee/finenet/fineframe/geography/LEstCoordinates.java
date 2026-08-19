package ee.finenet.fineframe.geography;

public class LEstCoordinates {
    private final Double x;
    private final Double y;

    public LEstCoordinates(Double x, Double y) {
        this.x = x;
        this.y = y;
    }

    public Double getX() {
        return x;
    }

    public Double getY() {
        return y;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;

        ee.finenet.fineframe.geography.LEstCoordinates that = (ee.finenet.fineframe.geography.LEstCoordinates) o;

        if (!x.equals(that.x)) return false;
        return y.equals(that.y);
    }

    @Override
    public int hashCode() {
        int result = x.hashCode();
        result = 31 * result + y.hashCode();
        return result;
    }

    @Override
    public String toString() {
        return "LEstCoordinates{" +
                "x=" + x +
                ", y=" + y +
                '}';
    }
}
