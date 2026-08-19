package ee.metsis.contracts;

import spark.Request;

import java.util.Optional;

import static ee.finenet.fineframe.utilities.NumbersUtility.parseIntSilent;
import static ee.finenet.fineframe.utilities.StringUtility.trimToNull;

public class HistoricalContractSearchFilter {

    private final String cadastre;
    private final String buyer;
    private final String seller;
    private final Integer offset;

    public HistoricalContractSearchFilter(Request req) {
        this.offset = parseIntSilent(req.queryParams("offset"));
        this.cadastre = trimToNull(req.queryParams("cadastre"));
        this.buyer = trimToNull(req.queryParams("buyer"));
        this.seller = trimToNull(req.queryParams("seller"));
    }

    public Optional<String> getCadastre() {
       return Optional.ofNullable(cadastre);
    }

    public Optional<String> getBuyer() {
        return Optional.ofNullable(buyer);
    }

    public Optional<String> getSeller() {
        return Optional.ofNullable(seller);
    }

    public int getOffset() {
        return offset ==  null ? 0 : offset;
    }
}
