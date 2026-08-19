package ee.rik.uuskinnisturaamat.services;

import org.apache.commons.csv.CSVFormat;
import org.apache.commons.csv.CSVParser;

import java.util.List;
import java.util.stream.Collectors;

import static java.util.Collections.emptyList;

public class ResponseCsvParser {

    private final CSVFormat csvFormat = CSVFormat.DEFAULT.withDelimiter(';');

    public List<String> parse(String responseContent) {
        try {
            if (responseContent == null || responseContent.isEmpty()) {
                return emptyList();
            }
            CSVParser csvParser = CSVParser.parse(responseContent, csvFormat);

            return csvParser.getRecords().stream()
                    .map(record -> record.get(2))
                    .filter(it -> it.matches("\\d{5}:\\d{3}:\\d{4}"))
                    .distinct()
                    .collect(Collectors.toList());
        } catch (Exception e) {
            throw new UusKinnisturaamatServiceException("Exception parsing response CSV", e);
        }

    }
}
