package ee.metsis.contracts.pdf;

import com.itextpdf.text.BaseColor;
import com.itextpdf.text.Chunk;
import com.itextpdf.text.Document;
import com.itextpdf.text.Element;
import com.itextpdf.text.Font;
import com.itextpdf.text.Image;
import com.itextpdf.text.Phrase;
import com.itextpdf.text.pdf.ColumnText;
import com.itextpdf.text.pdf.PdfPageEventHelper;
import com.itextpdf.text.pdf.PdfWriter;

public class HeaderFooterPageEvent extends PdfPageEventHelper {

    private static final Font FOOTER_FONT = new Font(Font.FontFamily.HELVETICA, 9.0f, 0, new BaseColor(144, 171, 207));

    private final String footer;
    private final byte[] headerBytes;

    public HeaderFooterPageEvent(byte[] headerBytes, String footer) {
        this.headerBytes = headerBytes;
        this.footer = footer;
    }

    public void onStartPage(PdfWriter writer, Document document) {
        if (headerBytes != null) {
            Image logo;
            try {
                logo = Image.getInstance(headerBytes);
            } catch (Exception e) {
                throw new RuntimeException(e);
            }
            logo.setAlignment(Image.ALIGN_LEFT);
            logo.scaleAbsoluteHeight(20);
            logo.scaleAbsoluteWidth(20);
            logo.scalePercent(100);
            Chunk chunk = new Chunk(logo, 0, -45);
            ColumnText.showTextAligned(writer.getDirectContent(), Element.ALIGN_CENTER, new Phrase(chunk), 150, 800, 0);
        }
    }

    public void onEndPage(PdfWriter writer, Document document) {
        if (footer != null) {
            String[] footerLines = footer.split("\n");
            int lineY = 20 + (footerLines.length) * 15;
            for (String footerLine : footerLines) {
                ColumnText.showTextAligned(writer.getDirectContent(), Element.ALIGN_CENTER, new Phrase(footerLine, FOOTER_FONT), 300, lineY, 0);
                lineY -= 15;
            }
        }
    }

}
