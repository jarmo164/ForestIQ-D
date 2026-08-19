package ee.metsis.contracts.pdf;

import com.itextpdf.html2pdf.HtmlConverter;
import ee.metsis.contracts.html.TemplateHtmlCreator;

import java.io.BufferedReader;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.UUID;

public class TemplateBasedDocumentCreator {

    private final TemplateHtmlCreator templateHtmlCreator;
    private final String tmpFolder;

    public TemplateBasedDocumentCreator(TemplateHtmlCreator templateHtmlCreator, String tmpFolder) {
        this.templateHtmlCreator = templateHtmlCreator;
        this.tmpFolder = tmpFolder;
    }

    public byte[] createPdf(ContractInput contract) {
        try {
            String html = templateHtmlCreator.create(contract);
            ByteArrayOutputStream pdfStream = new ByteArrayOutputStream();
            HtmlConverter.convertToPdf(html, pdfStream);
            return pdfStream.toByteArray();
        } catch (Exception e) {
            throw new RuntimeException("Creating PDF failed", e);
        }
    }

    public byte[] createWord(ContractInput contract) {
        try {
            String html = templateHtmlCreator.create(contract);
            return convertToWord(html);
        } catch (Exception e) {
            throw new RuntimeException("Creating Word document failed", e);
        }
    }

    private byte[] convertToWord(String html) throws IOException {
        String fileNameBody = randomSafeString();
        String htmlFile = tmpFolder + "/" + fileNameBody + ".html";
        String wordFile = tmpFolder + "/" + fileNameBody + ".docx";
        Files.write(Paths.get(htmlFile), html.getBytes(StandardCharsets.UTF_8));
        execPandoc(htmlFile, wordFile);
        return Files.readAllBytes(Paths.get(wordFile));
    }

    private String randomSafeString() {
        return UUID.randomUUID().toString().replaceAll("-", "");
    }

    private void execPandoc(String htmlFile, String wordFile) {
        try {
            ProcessBuilder processBuilder = new ProcessBuilder();
            processBuilder.command("ash", "-c", "/usr/local/bin/pandoc -f html " + htmlFile + " -o " + wordFile);
            System.out.println(processBuilder.command());

            Process process = processBuilder.start();

            StringBuilder output = new StringBuilder();

            BufferedReader reader = new BufferedReader(
                    new InputStreamReader(process.getInputStream()));

            String line;
            while ((line = reader.readLine()) != null) {
                output.append(line).append("\n");
            }

            int exitVal = process.waitFor();
            if (exitVal == 0) {
                System.out.println("Success!");
                System.out.println(output);
            } else {
                throw new IllegalStateException("Nonzero exitVal " + exitVal + " with output " + output);
            }
        } catch (Exception e) {
            throw new RuntimeException("Executing pandoc failed", e);
        }


    }
}
