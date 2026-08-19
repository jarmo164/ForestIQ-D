package ee.metsis.coordinates;

import ee.finenet.fineframe.geography.LEstCoordinates;
import ee.finenet.fineframe.geography.LatLng;

import java.util.Objects;

import static java.lang.Math.PI;
import static java.lang.Math.atan;
import static java.lang.Math.pow;
import static java.lang.Math.sin;

public class LEstGeoConverter {

    private static final double A = 6378137.0;
    private static final double ESQ = 0.006694380022903409;
    private static final double L0 = 0.4188788707025646;
    private static final double FN = 6375000.0;
    private static final double FE = 500000.0;
    private static final double N1 = 0.8541756676810336;
    private static final double FF = 1.7988478189672137;
    private final static double P0 = 4020208.636738494;

    public LatLng lEstToGeo(LEstCoordinates lEst) {
        Objects.requireNonNull(lEst, "LEstCoordinates lEst in LEstGeoConverter.lEstToGeo(LEstCoordinates lEst) must not be null");
        double xx = lEst.getX() - FN;
        double yy = lEst.getY() - FE;
        double p = pow((yy * yy + (P0 - xx) * (P0 - xx)), 0.5);
        double t = pow((p / (A * FF)), (1.0 / N1));
        double fii = atan(yy / (P0 - xx));
        double lon = fii / N1 + L0;
        double u = (PI / 2.0) - (2.0 * atan(t));
        double lat = u + (ESQ / 2.0 + (5.0 * pow(ESQ, 2) / 24.0) + (pow(ESQ, 3) / 12.0) +
                (13.0 * pow(ESQ, 4) / 360.0)) * sin(2.0 * u) +
                ((7.0 * pow(ESQ, 2) / 48.0) + (29.0 * pow(ESQ, 3) / 240.0) + (811.0 * pow(ESQ, 4) / 11520.0)) * sin(4.0 * u) +
                ((7.0 * pow(ESQ, 3) / 120.0) + (81.0 * pow(ESQ, 4) / 1120.0)) * sin(6.0 * u) + (4279.0 * pow(ESQ, 4) / 161280.0)
                * sin(8.0 * u);
        return new LatLng(rad2deg(lat), rad2deg(lon));
    }

    private static double rad2deg(double rad) {
        return rad * 180.0 / PI;
    }

}
