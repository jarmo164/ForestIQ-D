package ee.metsis.contracts;

import ee.finenet.fineframe.http.AbstractRequestHandler;
import ee.finenet.fineframe.http.Requestable;
import ee.finenet.fineframe.serialization.GsonHolder;
import ee.metsis.ServiceRegistry;
import ee.metsis.security.Privilege;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import spark.Request;
import spark.Response;

import java.sql.Date;
import java.time.Clock;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.Collection;
import java.util.Collections;

@Requestable("/contract")
public class ContractDataPreparationRequestHandler extends AbstractRequestHandler {

    private static final DateTimeFormatter DDMMYY = DateTimeFormatter.ofPattern("ddMMyy");

    private static final Logger logger = LoggerFactory.getLogger(ContractDataPreparationRequestHandler.class);

    private final Clock clock = Clock.systemDefaultZone();

    private final ContractService contractService;

    private final BuyerConfiguration buyerConfiguration;

    public ContractDataPreparationRequestHandler(ServiceRegistry serviceRegistry) {
        this.contractService = serviceRegistry.getContractService();
        this.buyerConfiguration = serviceRegistry.getBuyerConfiguration();
    }

    @Override
    protected ContractData handleRequest(Request req, Response res) {
        String baseContractId = req.queryParams("basecontract");
        return contractService.loadBaseContract(baseContractId).orElseGet(() -> {
            ContractData contractData = new ContractData();
            LocalDate now = LocalDate.now();
            contractData.setContractNumber(now.format(DDMMYY));
            ContractDetails contractDetails = new ContractDetails();
            ContractualCadastre cadastre = new ContractualCadastre();
            cadastre.setForestSections(Collections.emptyList());
            contractDetails.setCadastres(Collections.singletonList(cadastre));
            contractDetails.setBankDaysToPayUp(buyerConfiguration.getDaysToPayUp());
            contractDetails.setDateOfEnforcement(Date.valueOf(now));
            contractDetails.setBankDaysToPayUpCondition(false);
            contractDetails.setFinalDate(Date.valueOf(now.plusYears(1)));
            contractData.setContractDetails(contractDetails);
            SellerParty sp = new SellerParty();
            sp.setContactInformation(new ContactInformation());
            contractData.setSellers(Collections.singletonList(sp));
            contractData.setBuyer(buyerConfiguration.getBuyerParty());
            contractDetails.setAdditionalTerms(buyerConfiguration.getDefaultAdditionalTerms());
            contractData.setTemplateNumber(0);
            logger.info("Contract preparation data: {}", GsonHolder.GSON.toJson(contractData));
            return contractData;
        });
    }


    @Override
    protected Collection<String> requireAtLeastOneOfPrivileges() {
        return privileges(Privilege.ADMIN.name());
    }
}
