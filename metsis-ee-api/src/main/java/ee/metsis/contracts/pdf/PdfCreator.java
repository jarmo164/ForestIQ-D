package ee.metsis.contracts.pdf;

import com.itextpdf.text.BaseColor;
import com.itextpdf.text.Chunk;
import com.itextpdf.text.Document;
import com.itextpdf.text.DocumentException;
import com.itextpdf.text.Element;
import com.itextpdf.text.Font;
import com.itextpdf.text.PageSize;
import com.itextpdf.text.Paragraph;
import com.itextpdf.text.Rectangle;
import com.itextpdf.text.pdf.PdfPCell;
import com.itextpdf.text.pdf.PdfPTable;
import com.itextpdf.text.pdf.PdfWriter;
import ee.finenet.fineframe.exceptions.BadRequestException;
import ee.finenet.fineframe.exceptions.UnexpextedException;
import ee.metsis.contracts.BuyerParty;
import ee.metsis.contracts.ContactInformation;
import ee.metsis.contracts.ContractData;
import ee.metsis.contracts.ContractDetails;
import ee.metsis.contracts.ContractPartyProxy;
import ee.metsis.contracts.SellerParty;
import ee.metsis.contracts.TemplateSpecificsForBuyer;

import java.io.ByteArrayOutputStream;
import java.text.DecimalFormat;
import java.text.DecimalFormatSymbols;
import java.text.NumberFormat;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Locale;
import java.util.stream.Collectors;

import static ee.finenet.fineframe.utilities.DateUtility.estonianDate;

public abstract class PdfCreator {
    private static final Font TITLE_FONT = new Font(Font.FontFamily.TIMES_ROMAN, 14, Font.BOLD, BaseColor.BLACK);
    private static final Font EMPHASIZED_FONT = new Font(Font.FontFamily.TIMES_ROMAN, 11, Font.BOLD, BaseColor.BLACK);
    private static final Font REGULAR_FONT = new Font(Font.FontFamily.TIMES_ROMAN, 11, Font.NORMAL, BaseColor.BLACK);
    static final SimpleDateFormat DATE_FORMAT = new SimpleDateFormat("dd.MM.yyyy");

    private static final String EMPTY = "";

    private static final DecimalFormat moneyFormatter = createMoneyFormatter();

    private static DecimalFormat createMoneyFormatter() {
        DecimalFormat moneyFormatter = (DecimalFormat) NumberFormat.getCurrencyInstance(Locale.forLanguageTag("et"));
        DecimalFormatSymbols symbols = moneyFormatter.getDecimalFormatSymbols();
        symbols.setCurrencySymbol("");
        moneyFormatter.setDecimalFormatSymbols(symbols);
        return moneyFormatter;
    }

    public byte[] create(ContractData contractData, TemplateSpecificsForBuyer templateSpecificsForBuyer) {
        try {
            ContractDataValidator.validate(contractData);
            ByteArrayOutputStream documentStream = new ByteArrayOutputStream();
            Document document = createDocument(documentStream, templateSpecificsForBuyer);

            addTitle(contractData, document);

            ContractDetails contractDetails = contractData.getContractDetails();
            List<SellerParty> sellers = contractData.getSellers();
            BuyerParty buyer = contractData.getBuyer();

            addFirstSentence(document, contractDetails);

            addSellerIntroductions(document, sellers);

            addBuyerIntroduction(document, buyer);

            doCreate(document, contractData);

            addLastPageEndingFooter(document, contractData.getSellers(), contractData.getBuyer());
            document.close();
            return documentStream.toByteArray();
        } catch (DocumentException e) {
            throw new UnexpextedException("PDF creation failed", e);
        }
    }

    List<Chunk> createWhichSellerGetsWhatChunks(SellerParty sellerParty) {
        return Arrays.asList(
                boldChunk(sellerParty.getName()),
                normalChunk(" kontole "),
                boldChunk(sellerParty.getBankAccountNumber()),
                normalChunk(String.format(" summa %s EUR.", sellerParty.getMoneyObtainedFromTheDeal()))
        );
    }

    String formatMoney(Double d) {
        String formatted = moneyFormatter.format(d);
        return formatted.endsWith(",00") ? formatted.substring(0, formatted.length() - 3) : formatted;
    }

    Chunk normalChunk(String text) {
        return new Chunk(text, REGULAR_FONT);
    }

    Chunk boldChunk(String text) {
        return new Chunk(text, EMPHASIZED_FONT);
    }

    List<Chunk> createSentenceFromChunks(List<List<Chunk>> sentenceParts) {
        List<Chunk> result = new ArrayList<>(sentenceParts.get(0));
        for (int i = 1; i < sentenceParts.size() - 1; i++) {
            result.add(normalChunk(", "));
            result.addAll(sentenceParts.get(i));
        }
        if (sentenceParts.size() > 1) {
            result.add(normalChunk(" ja "));
            result.addAll(sentenceParts.get(sentenceParts.size() - 1));
        }
        return result;
    }

    void addParagraph(Document document, Chunk... chunks) throws DocumentException {
        Paragraph p = new Paragraph();
        p.setSpacingBefore(5);
        p.setSpacingAfter(5);
        p.addAll(Arrays.asList(chunks));
        document.add(p);
    }

    private void addLastPageEndingFooter(Document document, List<SellerParty> sellers, BuyerParty buyer) throws DocumentException {
        addParagraph(document, boldChunk("Poolte andmed:"));

        PdfPTable endingBlocks = new PdfPTable(2);

        endingBlocks.setWidthPercentage(100);

        List<Chunk> sellerFooterChunks = new ArrayList<>();

        sellers.forEach(sellerParty -> {
            String code = sellerParty.getCode();
            sellerFooterChunks.add(boldChunk((sellerParty.getName() + " " + (sellerParty.seemsPrivatePerson() ? " (isikukood " + code + ")" : code)) + "\n"));
            ContactInformation sellerContacts = sellerParty.getContactInformation();
            if (sellerContacts.getAddress() != null) {
                sellerFooterChunks.add(boldChunk(sellerContacts.getAddress() + "\n"));
            }
        });
        ContactInformation sellerContacts = sellers.stream()
                .filter(s -> s.getContactInformation().getPhoneNo() != null)
                .findFirst().orElseThrow(
                        () -> new BadRequestException("ILLEGAL_CONTRACT_INPUT_NO_SELLER_HAS_PHONE_NO")
                ).getContactInformation();
        sellerFooterChunks.add(normalChunk(sellerContacts.getEmail() + "\n"));
        sellerFooterChunks.add(normalChunk("Tel. " + sellerContacts.getPhoneNo() + "\n"));

        PdfPCell leftCell = new PdfPCell();
        leftCell.setPadding(0);
        sellerFooterChunks.forEach(leftCell::addElement);
        leftCell.addElement(boldChunk("Allkirjastatud digitaalselt."));
        leftCell.setHorizontalAlignment(Element.ALIGN_LEFT);
        leftCell.setBorder(Rectangle.NO_BORDER);
        endingBlocks.addCell(leftCell);

        List<Chunk> buyerFooterChunks = new ArrayList<>();
        ContactInformation buyerContacts = buyer.getContactInformation();
        buyerFooterChunks.add(boldChunk(buyer.getName() + " " + (buyer.seemsPrivatePerson() ? "(isikukood: " + buyer.getCode() + ")" : buyer.getCode()) + "\n"));
        if (buyerContacts.getAddress() != null) {
            buyerFooterChunks.add(boldChunk(buyerContacts.getAddress() + "\n"));
        }
        if (buyer.hasProxy()) {
            ContractPartyProxy buyerProxy = buyer.getProxy();
            buyerFooterChunks.add(boldChunk("\n" + buyerProxy.getName() + " " + buyerProxy.getCode() + "\n"));
        }
        buyerFooterChunks.add(normalChunk(buyerContacts.getEmail() + "\n"));
        buyerFooterChunks.add(normalChunk("Tel.  " + buyerContacts.getPhoneNo() + "\n"));

        PdfPCell rightCell = new PdfPCell();
        rightCell.setPaddingLeft(10);
        buyerFooterChunks.forEach(rightCell::addElement);
        rightCell.setHorizontalAlignment(Element.ALIGN_LEFT);
        rightCell.setBorder(Rectangle.NO_BORDER);
        endingBlocks.addCell(rightCell);

        document.add(endingBlocks);
    }


    private Document createDocument(ByteArrayOutputStream documentStream, TemplateSpecificsForBuyer templateSpecificsForBuyer) throws DocumentException {
        Rectangle pageSize = PageSize.A4;
        int marginLeft = 65;
        int marginRight = 65;
        int marginTop = 100;
        int marginBottom = 100;
        Document document = new Document(pageSize, marginLeft, marginRight, marginTop, marginBottom);
        PdfWriter pdfWriter = PdfWriter.getInstance(document, documentStream);
        pdfWriter.setPageEvent(new HeaderFooterPageEvent(templateSpecificsForBuyer.getHeaderLogo(), templateSpecificsForBuyer.getFooterText()));
        document.open();
        return document;
    }

    private void addTitle(ContractData contractData, Document document) throws DocumentException {
        Paragraph title = new Paragraph("KASVAVA METSA RAIEÕIGUSE VÕÕRANDAMISE LEPING nr " + contractData.getContractNumber(), TITLE_FONT);
        title.setSpacingAfter(13);
        document.add(title);
    }

    private void addFirstSentence(Document document, ContractDetails contractDetails) throws DocumentException {
        Paragraph contractIsMadeAtParagraph =
                new Paragraph("Käesolev Leping on sõlmitud " + estonianDate(contractDetails.getDateOfEnforcement()) + " digitaalselt.", EMPHASIZED_FONT);
        document.add(contractIsMadeAtParagraph);
    }

    private void addSellerIntroductions(Document document, List<SellerParty> sellers) throws DocumentException {
        List<String> sellerIntroductions = createSellerIntroductions(sellers);
        Paragraph sellerIntroductionParagraph = new Paragraph(20);
        sellerIntroductionParagraph.add(new Chunk(createEnumerationString(sellerIntroductions), EMPHASIZED_FONT));
        sellerIntroductionParagraph.add(new Chunk(" (edaspidi nimetatud MÜÜJA) ja ", REGULAR_FONT));
        document.add(sellerIntroductionParagraph);
    }

    private void addBuyerIntroduction(Document document, BuyerParty buyer) throws DocumentException {
        Paragraph buyerIntroduction = new Paragraph(20);
        buyerIntroduction.add(boldChunk(createBuyerPartyText(buyer)));
        buyerIntroduction.add(normalChunk((buyer.hasProxy() ? " isikus, kes tegutseb põhikirja alusel" : EMPTY) +
                " (edaspidi nimetatud OSTJA), keda nimetatakse edaspidi käesolevas " +
                "Lepingus Pool või koos Poolteks, sõlmisid käesoleva Lepingu, edaspidi Lepingu, alljärgnevas:"));
        buyerIntroduction.setSpacingAfter(20);
        document.add(buyerIntroduction);
    }

    private List<String> createSellerIntroductions(List<SellerParty> sellers) {
        return sellers.stream().map(this::createSellerPartyText).collect(Collectors.toList());
    }

    private String createSellerPartyText(SellerParty party) {
        String code = party.getCode();
        return party.getName() + " (" + (party.seemsPrivatePerson() ? "isikukood " : EMPTY) + code + ")";
    }

    private String createBuyerPartyText(BuyerParty party) {
        String code = party.getCode();
        String partyText = party.getName() + " (" + (party.seemsPrivatePerson() ? "isikukood " : EMPTY) + code + ")";
        if (party.hasProxy()) {
            partyText += (", " + createProxyText(party.getProxy()));
        }
        return partyText;
    }

    private String createProxyText(ContractPartyProxy proxy) {
        String code = proxy.getCode();
        return proxy.getName() + " (isikukood " + code + ")";
    }

    String createEnumerationString(List<String> sellerIntros) {
        StringBuilder sellerIntrosText = new StringBuilder(sellerIntros.get(0));
        for (int i = 1; i < sellerIntros.size() - 1; i++) {
            sellerIntrosText.append(", ").append(sellerIntros.get(i));
        }
        if (sellerIntros.size() > 1) {
            sellerIntrosText.append(" ja ").append(sellerIntros.get(sellerIntros.size() - 1));
        }
        return sellerIntrosText.toString();
    }

    protected abstract void doCreate(Document document, ContractData contractData) throws DocumentException;
}
