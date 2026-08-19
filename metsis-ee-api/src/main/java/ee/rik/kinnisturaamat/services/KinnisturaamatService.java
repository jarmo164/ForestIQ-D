package ee.rik.kinnisturaamat.services;

import ee.rik.kinnisturaamat.configuration.KinnisturaamatServiceConfiguration;
import rik.kinniskrteenused.KRTeenusSoap;
import rik.kinniskrteenused.ObjektideArv;

import java.net.URL;

import javax.xml.namespace.QName;
import javax.xml.ws.Service;

public class KinnisturaamatService {

    private final KinnisturaamatServiceConfiguration configuration;

    public KinnisturaamatService(KinnisturaamatServiceConfiguration configuration) {
        this.configuration = configuration;
    }

    public int getCadastreCount(CadastreCountRequest req) {
        try {
            URL wsdlURL = new URL("https://kinnistusraamat.rik.ee/krteenused/kr_teenus.asmx?WSDL");
            QName SERVICE_NAME = new QName("http://kinnistusraamat.rik.ee/krteenused/", "KR_teenus");
            Service service = Service.create(wsdlURL, SERVICE_NAME);
            KRTeenusSoap client = service.getPort(KRTeenusSoap.class);
            String code = req.getCode();
            String firstName = req.getType() == CadastreCountRequest.OwnerType.FIRMAD ? "1" : req.getName().split(" ")[0];
            String lastName = req.getType() == CadastreCountRequest.OwnerType.FIRMAD ? req.getName() : req.getName().substring(req.getName().lastIndexOf(" ") + 1).trim();
            String serviceUser = configuration.getLoginUsername();
            String servicePassword = configuration.getLoginPassword();
            ObjektideArv objektideArv = client.objektideArv(code, firstName, lastName, serviceUser, servicePassword);
            String veateade = objektideArv.getVeateade();
            if (veateade != null) {
                throw new KinnisturaamatServiceException(veateade);
            }
            return Integer.parseInt(objektideArv.getArv());
        } catch (KinnisturaamatServiceException e) {
            throw e;
        } catch (Exception e) {
            throw new KinnisturaamatServiceException("Fetching cadastre count failed", e);
        }
    }
}
