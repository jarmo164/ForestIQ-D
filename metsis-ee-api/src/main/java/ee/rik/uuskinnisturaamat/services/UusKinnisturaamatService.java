package ee.rik.uuskinnisturaamat.services;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.Collections;
import java.util.List;

public class UusKinnisturaamatService {

    private static final Logger logger = LoggerFactory.getLogger(UusKinnisturaamatService.class);

    private final ResponseCsvParser responseCsvParser = new ResponseCsvParser();

    public List<String> getOwnerProperties(String ownerCode) {

        try {
            String url = "https://uuskinnistusraamat.rik.ee/default" +
                    ".aspx?LoadToFile=true&oi=&ko=&tbxAadress=&KatasterKinnistuNr=&IKRKOmanik=" + ownerCode +
                    "&FrontPageTerm=&isKorteriYhistuJuhatuseLiige=False&kasutajaRiik=&format=csv";
            return responseCsvParser.parse(
                    httpGet(url)
            );
        } catch (Exception e) {
            logger.error("Something went wrong while communicating with Uuskinnisturaamat", e);
            return Collections.emptyList();
        }
    }

    private String shortenIfNeeded(String str) {
        if (str == null) {
            str = "";
        }
        String endPrefix = str.length() > 100 ? " ..." : "";
        return str.substring(0, Math.min(str.length(), 100)) + endPrefix;
    }

    private String httpGet(String address) {
        try {
            URL url = new URL(address);
            HttpURLConnection connection = (HttpURLConnection) url.openConnection();
            connection.setRequestMethod("GET");
            connection.connect();
            StringBuilder result = new StringBuilder();
            try (BufferedReader br = new BufferedReader(new InputStreamReader(connection.getInputStream()))) {
                String inputLine;
                while (true) {
                    inputLine = br.readLine();
                    if (inputLine == null) {
                        break;
                    }
                    result.append(inputLine).append("\n");
                }
            }
            return result.toString();
        } catch (Exception e) {
            throw new UusKinnisturaamatServiceException("Exception during HTTP GET " + address, e);
        }
    }
}
