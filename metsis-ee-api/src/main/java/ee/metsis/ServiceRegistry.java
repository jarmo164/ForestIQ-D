package ee.metsis;

import com.auth0.jwt.algorithms.Algorithm;
import ee.finenet.fineframe.exceptions.ConfigurationException;
import ee.finenet.fineframe.security.AuthConfiguration;
import ee.finenet.fineframe.security.AuthenticationService;
import ee.finenet.fineframe.security.password.BCryptBasedPasswordHandler;
import ee.finenet.fineframe.security.password.PasswordHandler;
import ee.finenet.fineframe.security.token.Jwt;
import ee.finenet.fineframe.security.token.TokenService;
import ee.finenet.fineframe.user.UserService;
import ee.maaamet.geoportaal.xgis.MaaametGeoportaalService;
import ee.metsad.register.services.ForestRegistryService;
import ee.metsis.admin.ownerstatusadministration.OwnerStatusDao;
import ee.metsis.admin.ownerstatusadministration.OwnerStatusService;
import ee.metsis.configuration.AppGeneralConfiguration;
import ee.metsis.configuration.SimoApiConfiguration;
import ee.metsis.contracts.BuyerConfiguration;
import ee.metsis.contracts.ContractDao;
import ee.metsis.contracts.ContractService;
import ee.metsis.contracts.autocompleters.AutoCompleterDao;
import ee.metsis.contracts.autocompleters.AutoCompleterService;
import ee.metsis.contracts.html.TemplateHtmlCreator;
import ee.metsis.contracts.pdf.TemplateBasedDocumentCreator;
import ee.metsis.messages.MessagesDao;
import ee.metsis.messages.MessagesService;
import ee.metsis.ownercadastre.api.OwnerCadastreApi;
import ee.metsis.ownercadastre.worker.OwnerCadastreWorker;
import ee.metsis.owners.OwnerDAO;
import ee.metsis.owners.OwnerService;
import ee.metsis.owners.logservice.OwnerLogDao;
import ee.metsis.owners.logservice.OwnerLogService;
import ee.metsis.personsdump.PersonsDumpDao;
import ee.metsis.personsdump.PersonsDumpService;
import ee.metsis.pria.CadastrePolygonService;
import ee.metsis.reminders.RemindersDao;
import ee.metsis.reminders.RemindersService;
import ee.metsis.users.MetsisEEUserService;
import ee.metsis.users.UserDAO;
import ee.metsis.users.UserOwnerStatusChangeStatisticsDAO;
import ee.metsis.users.statistics.UserStatisticsService;
import ee.metsis.workers.LastOwnersUpdateDao;
import ee.pria.kls.kaart.geootsing.PriaCadastrePolygonService;
import org.bouncycastle.jce.provider.BouncyCastleProvider;

import java.nio.file.Files;
import java.nio.file.Paths;
import java.security.Security;

import javax.sql.DataSource;

public class ServiceRegistry {

    static {
        Security.addProvider(new BouncyCastleProvider());
    }

    private final UserService userService;
    private final Jwt jwt;
    private final AuthenticationService authenticationService;
    private final PasswordHandler passwordHandler;
    private final OwnerService ownerService;
    private final OwnerLogService ownerLogService;
    private final UserStatisticsService userStatisticsService;
    private final AutoCompleterService autoCompleterService;
    private final ContractService contractService;
    private final OwnerStatusService ownerStatusService;
    private final PersonsDumpService personsDumpService;
    private final RemindersService remindersService;
    private final MessagesService messagesService;
    private final BuyerConfiguration buyerConfiguration;
    private final OwnerCadastreWorker ownerCadastreWorker;
    private final OwnerDAO ownerDAO;

    public ServiceRegistry(DataSource dataSource, AuthConfiguration authConfiguration,
                           AppGeneralConfiguration appGeneralConfiguration, BuyerConfiguration buyerConfiguration,
                           SimoApiConfiguration simoApiConfiguration) {
        final String tmpFolder = "/tmp/metsis";
        try {
            Files.createDirectories(Paths.get(tmpFolder));
        } catch (Exception e) {
            throw new RuntimeException("Creating tmp folder failed", e);
        }
        this.buyerConfiguration = buyerConfiguration;
        this.passwordHandler = new BCryptBasedPasswordHandler();
        OwnerDAO ownerDAO = new OwnerDAO(dataSource);
        UserDAO userDAO = new UserDAO(dataSource);
        this.userService = new MetsisEEUserService(userDAO, ownerDAO);
        OwnerStatusDao ownerStatusDao = new OwnerStatusDao(dataSource);
        this.ownerStatusService = new OwnerStatusService(ownerStatusDao, ownerDAO);
        this.userStatisticsService = new UserStatisticsService(userDAO, new UserOwnerStatusChangeStatisticsDAO(dataSource), ownerStatusService);
        Algorithm algorithm = initAlorithm();
        this.jwt = new Jwt(algorithm);
        boolean isDevMode = appGeneralConfiguration.isDevMode();
        this.authenticationService = new AuthenticationService(userService, new TokenService(authConfiguration), passwordHandler, isDevMode);
        RemindersDao remindersDao = new RemindersDao(dataSource);
        this.messagesService = new MessagesService(new MessagesDao(dataSource));
        this.ownerLogService = new OwnerLogService(new OwnerLogDao(dataSource));
        this.ownerService = new OwnerService(
                ownerDAO,
                userDAO,
                ownerStatusService,
                ownerLogService,
                userService,
                new MaaametGeoportaalService(),
                new CadastrePolygonService(new PriaCadastrePolygonService()),
                messagesService,
                new ForestRegistryService());
        this.autoCompleterService = new AutoCompleterService(new AutoCompleterDao(dataSource), ownerService);
        this.contractService = new ContractService(
                new ContractDao(dataSource),
                new TemplateBasedDocumentCreator(new TemplateHtmlCreator(), tmpFolder)
        );
        this.personsDumpService = new PersonsDumpService(new PersonsDumpDao(dataSource));
        this.remindersService = new RemindersService(remindersDao, ownerService, ownerLogService);
        this.ownerCadastreWorker = new OwnerCadastreWorker(
                new OwnerCadastreApi(simoApiConfiguration.getEndpoint(), simoApiConfiguration.getToken()),
                ownerService,
                new LastOwnersUpdateDao(dataSource)
        );
        this.ownerDAO = ownerDAO;
    }

    private static Algorithm initAlorithm() {
        try {
            return Algorithm.HMAC256("2a023fb2-585b-4782-b49c-cd10b0a79b77");
        } catch (Exception e) {
            throw new ConfigurationException("Initializing token signing algorithm failed", e);
        }
    }

    public UserService getUserService() {
        return userService;
    }

    public Jwt getJwt() {
        return jwt;
    }

    public AuthenticationService getAuthenticationService() {
        return authenticationService;
    }

    public PasswordHandler getPasswordHandler() {
        return passwordHandler;
    }

    public OwnerService getOwnerService() {
        return ownerService;
    }

    public OwnerDAO getOwnerDAO() {
        return ownerDAO;
    }

    public OwnerLogService getOwnerLogService() {
        return ownerLogService;
    }

    public UserStatisticsService getUserStatisticsService() {
        return userStatisticsService;
    }

    public AutoCompleterService getAutoCompleterService() {
        return autoCompleterService;
    }

    public ContractService getContractService() {
        return contractService;
    }

    public OwnerStatusService getOwnerStatusService() {
        return ownerStatusService;
    }

    public PersonsDumpService getPersonsDumpService() {
        return personsDumpService;
    }

    public RemindersService getRemindersService() {
        return remindersService;
    }

    public MessagesService getMessagesService() {
        return messagesService;
    }

    public BuyerConfiguration getBuyerConfiguration() {
        return buyerConfiguration;
    }

    OwnerCadastreWorker getOwnerCadastreWorker() {
        return ownerCadastreWorker;
    }
}
