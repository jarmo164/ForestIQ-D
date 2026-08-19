package ee.metsis.contracts.pdf;

import com.itextpdf.text.Chunk;
import com.itextpdf.text.Document;
import com.itextpdf.text.DocumentException;
import com.itextpdf.text.Element;
import com.itextpdf.text.Phrase;
import com.itextpdf.text.pdf.PdfPCell;
import com.itextpdf.text.pdf.PdfPTable;
import ee.metsis.contracts.ContractData;
import ee.metsis.contracts.ContractDetails;
import ee.metsis.contracts.ContractualCadastre;
import ee.metsis.contracts.ForestSection;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.stream.Collectors;

public class WithForrestPlanPdfCreator extends PdfCreator {

    public void doCreate(Document document, ContractData contractData) throws DocumentException {

        ContractDetails contractDetails = contractData.getContractDetails();

        addParagraph(document, boldChunk("1. Üldsätted"));

        addParagraph(document, normalChunk("1.1. Müüja kinnitab, et käesoleva Lepingu objektiks oleva kasvava metsa raieõiguse Müüja poolt " +
                "valdamine on seaduslik ja Ostja kinnitab, et ta on selles veendunud."));

        addParagraph(document, boldChunk("2. Lepingu dokumendid"));

        addParagraph(document, normalChunk("2.1. Lepingu dokumendid koosnevad käesolevast Lepingust, Lepingu lisadest ning Lepingu " +
                "muudatustest, milles lepitakse kokku pärast Lepingule allakirjutamist. "));

        addParagraph(document, boldChunk("3. Lepingu objekt"));

        addParagraph(document, normalChunk("3.1. Müüja müüb ja Ostja ostab kasvava metsa raieõiguse "),
                boldChunk(String.format("%s.", createEnumerationString(
                        contractDetails.getCadastres().stream().map(this::createCadastreString).collect(Collectors.toList())
                ))));

        addParagraph(document, normalChunk("3.2. Kasvava metsa raieõiguse omandamine annab Ostjale õiguse langetada puid Lepingus " +
                "fikseeritud ulatuses, kohas, ajal ja tingimustel ning valmistada nendest puudest puidusortimente ja " +
                "saadud sortimendid ära vedada."));

        addCadastresTable(document, contractDetails);

        addParagraph(document, normalChunk("3.4. Ostja on raielangiga tutvunud ja tema poolt Müüjale pretensioone ostetud kasvava metsa raieõiguse kohta ei ole."));

        addParagraph(document, boldChunk("4. Raieõiguse müügihind"));
        addParagraph(document, normalChunk(String.format("4.1. Kasvava metsa raieõiguse müügihind on %s eurot.",
                formatMoney(contractDetails.getPrice()))));

        addParagraph(document, boldChunk("5. Maksetingimused"));
        List<List<Chunk>> sentenceParts = contractData.getSellers().stream().map(this::createWhichSellerGetsWhatChunks).collect(Collectors.toList());
        List<Chunk> whoGetsWhatSentence = new ArrayList<>();
        whoGetsWhatSentence.add(normalChunk("5.1. Ostja tasub kasvava metsa raieõiguse võõrandamise eest Müüja "));
        whoGetsWhatSentence.addAll(createSentenceFromChunks(sentenceParts));
        addParagraph(document, whoGetsWhatSentence.toArray(new Chunk[whoGetsWhatSentence.size()]));

        if (contractData.getContractDetails().isBankDaysToPayUpCondition()) {
            addParagraph(document, normalChunk(String.format("5.2. Ostja tasub käesoleva Lepingu punktis 4.1 " +
                    "nimetatud ostuhinna hiljemalt %s pangapäeva jooksul pärast metsateatiste allkirjastamist " +
                    "Keskkonnaameti poolt.", contractData.getContractDetails().getBankDaysToPayUp())));
        } else {
            addParagraph(document, normalChunk(String.format("5.2. Ostja tasub käesoleva Lepingu punktis 4.1 " +
                    "nimetatud ostuhinna hiljemalt %s pangapäeva jooksul pärast Lepingu allkirjastamist.",
                    contractData.getContractDetails().getBankDaysToPayUp())));
        }

        addParagraph(document, boldChunk("6. Kasvava metsa ülestöötamise- ja kokkuveo tingimused ja tähtajad"));
        addParagraph(document, normalChunk("6.1. Kasvava metsa raieõiguse omandanud Ostja kohustub järgima metsaseaduses sätestatud raieõiguse sisu."));
        addParagraph(document, normalChunk("6.2. Kasvava metsa raieõigusega kaasneb õigus kasutada maad vastavalt " +
                "raieõiguse sisule."));
        addParagraph(document, normalChunk("6.3. Ostja on kohustatud kasvava metsa üles töötama hiljemalt "), boldChunk(String.format("%s.", DATE_FORMAT.format(contractDetails.getFinalDate()))));
        addParagraph(document, normalChunk("6.4. Ostja kohustab ülestöötatud metsamaterjali kokku vedama hiljemalt "),
                boldChunk(DATE_FORMAT.format(contractDetails.getFinalDate())), normalChunk(". Ostja kirjalikul taotlusel võib Müüja mõjuvatel põhjustel tähtaega " +
                        "pikendada. Tähtaja pikendamine vormistatakse kirjalikult."));

        addParagraph(document, boldChunk("6.5. Ostja on kohustatud:"));
        addParagraph(document, normalChunk("6.5.1. Metsa ülestöötamisel ja kokkuveol järgima metsaseaduse ja päästeseaduse ning nende alusel antud õigusaktide norme ja tegema kõik endast oleneva, et vältida metsa tervisliku seisundi halvenemist ja tuleohtu, samuti rakendama tehnoloogiaid ja tehnilisi vahendeid, mis ei kahjusta kasvavat metsa, pinnast ja ümbritsevat keskkonda;"));
        addParagraph(document, normalChunk("6.5.2. Lageraie teostamisel on Ostja kohustatud puhastama pärast tööde " +
                "lõpetamist raielangi. Raiekoha puhastamise viis on raiejäätmete koondamine hunnikutesse ja hilisem hakkimine või raiejäätmete kasutamine kokkuveoteede tugevdamiseks."));
        addParagraph(document, normalChunk("6.5.3. Hoidma omal kulul funktsionaalses korras teed, kvartalisihid, " +
                "veejuhtmed ja nendele ehitatud rajatised, kus toimub metsavarumine ja sellega seotud tegevus (metsamaterjali kokkuvedu)."));
        addParagraph(document, normalChunk("6.5.4. Parandama kokkuveo käigus lõhutud teed, truubid , sillad ja teised rajatised omal kulul."));
        addParagraph(document, normalChunk("6.5.5. Täitma metsades tuleohutuse eeskirju ning tulekahju puhkemisel informeerima koheselt päästeameti häirekeskust, Müüjat ning keskkonna valvetöötajaid ja teostama kustutustöid"));
        addParagraph(document, normalChunk("6.5.6. Täitma Müüja nõudeid metsaseaduse ja teiste õigusaktide normide, samuti Lepingu tingimuste täitmiseks;"));
        addParagraph(document, normalChunk("6.6. Kasvava metsa raieõiguse pantimine ei ole lubatud."));
        addParagraph(document, normalChunk(String.format("6.7. Raiumise eritingimused: %s", Optional.ofNullable(contractDetails.getAdditionalTerms()).orElse(" ei ole."))));

        addParagraph(document, boldChunk("6.8. Ostjal on õigus:"));
        addParagraph(document, normalChunk("6.8.1. Alustada raie teostamist hetkest, mil ostusumma on üle kantud " +
                "Müüja pangaarvele"));

        addParagraph(document, boldChunk("6.9. Müüja kohustub:"));

        List<String> notificationIds = contractDetails.getCadastres().stream().flatMap(e -> e.getForestSections().stream()).map(ForestSection::getNotificationId).filter(Objects::nonNull).distinct().collect(Collectors.toList());
        if (notificationIds.isEmpty()) {
            addParagraph(document, normalChunk("6.9.1. Üle andma Ostjale raielangid."));
        } else if (notificationIds.size() == 1) {
            addParagraph(document, normalChunk("6.9.1. Üle andma Ostjale raielangid, vastavalt Metsateatisele nr "), boldChunk(notificationIds.get(0)), normalChunk("."));
        } else {
            addParagraph(document, normalChunk("6.9.1. Üle andma Ostjale raielangid, vastavalt Metsateatistele nr "), boldChunk(createEnumerationString(notificationIds)), normalChunk("."));
        }
        addParagraph(document, normalChunk("6.9.2. Võimaldama Ostjale teostada raieõigust Lepingus sätestatud " +
                "tähtajal, selleks ise mitte raiuma, mitte lubama kolmandatel isikutel raiuda metsa raieõiguse " +
                "ulatuse alalt ega tegema muid tegusid, mis võivad takistada Ostjal Lepinguga antud õiguste " +
                "teostamist,"));
        addParagraph(document, normalChunk("6.9.3. Pikendama metsateatist, kui ilmastikuolud ei võimalda raietöid teostada metsateatise kehtivuse ajal. Metsateatise pikendamisel sõlmitakse lepingu lisa."));

        addParagraph(document, boldChunk("6.10. Müüjal on õigus:"));
        addParagraph(document, normalChunk("6.10.1. Tulekaitse kaalutlustel, metsa ökosüsteemi või sihtide, teede ja teiste rajatiste kaitseks peatada või keelata metsa, sihtide, teede ja teiste rajatiste kasutamine kui ilmastikutingimused ei võimalda metsa või nimetatud rajatisi kasutada ilma metsa või rajatisi kahjustamata või ohtu seadmata. "));
        addParagraph(document, normalChunk("6.10.2. Teostada kontrolli Ostja poolt raielangil tehtavate tööde üle ning vajadusel, kui Ostja ei täida või rikub seaduses ja Lepingus sätestatud tingimusi, peatada tööde tegemine kuni Müüja nõuete täitmiseni;"));
        addParagraph(document, normalChunk("6.10.3. Juhul kui Ostja ei täida p. 6.5.2 kohustust on Müüjal ühepoolselt õigus akteerida ülestöötatud raielangid. Aktis märgitud puudused, mille täitmine on pandud kohustuseks Ostjale käesoleva Lepinguga või seadusega, kohustub Ostja kõrvaldama omal kulul aktis märgitud tähtaja jooksul. Juhul kui puudused kõrvaldab Müüja, kohustub Ostja vajalikud kulutused Müüjale hüvitama 10 päeva jooksul vastava arve saamisest."));
        addParagraph(document, normalChunk("6.10.4. Juhul, kui Müüjal tekib raietööde käigus pretensioone Ostja poolt" +
                " kasutatavale tehnikale, akteerib ta selle mittevastavusena ning määrab Ostjale tähtaja puuduste kõrvaldamiseks, vajadusel raietööd seniks peatatakse"));

        addParagraph(document, boldChunk("7. Seemnepuude ja metsa võtmebiotoopide kaitse ja säilitamise tingimused ning raiel jälgitavad looduskaitse tingimused."));
        addParagraph(document, normalChunk("7.1. Võtmebiotoobi (vääriselupaiga) kaitse toimub metsa majandajale Keskkonnaministeeriumi poolt väljastatud ettekirjutuse kohaselt. Kasvava metsa raieõiguse müügiga läheb ettekirjutuse täitmine üle raieõiguse omandajale. Ettekirjutus lisatakse käesolevale Lepingule."));
        addParagraph(document, normalChunk("7.2. Ostja on kohustatud järgima metsaseaduses ja teistes õigusaktides sätestatut ning säilitama säilik- ja seemnepuud, et tagada metsa uuenemiseks vajalikud tingimused. "));
        addParagraph(document, normalChunk("7.3. Ostja on kohustatud raiel järgima järgmisi looduskaitsetingimusi: puuduvad."));

        addParagraph(document, boldChunk("8. Riski üleminek"));
        addParagraph(document, normalChunk("8.1. Kasvava metsa juhusliku hävimise riisiko läheb Müüjalt Ostjale üle " +
                "pärast Lepingule alla kirjutamist ja ostuhinna tasumist. "));
        addParagraph(document, normalChunk("8.2. Õigusaktidele tuginevad keskkonnajärelevalve asutuste ettekirjutused ja otsused ning nende asutuste keskkonnakaitseinspektorite ettekirjutused on Ostjale kohustuslikud. Nendest ettekirjutustest tulenevate võimalike kahjude eest Ostjale Müüja ei vastuta."));

        addParagraph(document, boldChunk("9. Poolte vastutus Lepingutingimuste rikkumisel"));
        addParagraph(document, normalChunk("9.1. Müüjal on õigus Leping ennetähtaegselt lõpetada juhtudel, kui Ostja ei täida talle Lepinguga pandud kohustusi."));
        addParagraph(document, normalChunk("9.2 Kui Ostja jätab lepingu punktis 4.1 ja 5.2 sätestatud tähtaegadel ja korras ostuhinna tasumata, loetakse leping kokkuleppeliselt lõppenuks. Sel juhul pooltel Lepingust tulenevaid õigusi ja kohustusi ei teki ning pooltel ei ole lepingu alusel üksteise suhtes õigust nõuda mistahes tasusid (sh pole Müüjal õigust nõuda Ostjalt tasu raieõiguse eest ega kasvava metsa väärtusele vastavat tasu) ega ka kahju hüvitamist."));
        addParagraph(document, normalChunk("9.3. Müüjalt Lepingu ennetähtaegse lõpetamise teate saamisel kohustub Ostja koheselt lõpetama raietööd langil, tagastama raielangi Lepingu ennetähtaegse lõpetamise teate saamise päevast ning hüvitama Müüja poolt nõutava kahju."));
        addParagraph(document, normalChunk("9.4 Ostja on kohustatud Müüjale hüvitama metsaseaduse ja sellest tulenevate õigusaktide rikkumisega tekitatud kahju, lähtudes looduskekkonnale tekitatud kahju hüvitamiseks kehtestatud korrast ja tingimustest. "));
        addParagraph(document, normalChunk("9.5. Kui Lepingu rikkumisega Ostja poolt kaasneb kriminaal- või halduskorras karistatav tegu, järgneb vastutus seaduses ettenähtud korras."));
        addParagraph(document, normalChunk("9.6. Kui Müüja on esitanud valeandmeid raieõiguse kuulumise või raie teostamise seaduspärasuse suhtes või teeb Ostjale takistusi raieõiguse teostamiseks, on Müüja kohustatud hüvitama Ostjale tekitatud kahju - tasuma tegelikult teostatud tööde eest ning leppetrahvi 10% tehingu hinnangulisest väärtusest."));
        addParagraph(document, normalChunk("9.7. Ostjal on õigus kasutada Lepingu objektiks olevat kinnistut " +
                "aastaringselt lisaks raieõiguse teostamisele ka raieõiguse teostamiseks vajaliku tehnikaga " +
                "liikumiseks (eelkõige olemasolevaid teid ja teede puudumisel Müüjaga eelnevalt kooskõlastatud alal)." +
                " Nimetatud alade kasutamise eest Müüja Lepingu kehtivuse ajal või kokkulepitud ajapikenduse jooksul " +
                "tasu ei nõua."));

        addParagraph(document, boldChunk("10. Vääramatu jõud"));
        addParagraph(document, normalChunk("10.1. Pool vabaneb vastutusest Lepingust tulenevate kohustuste mittetäitmise või mittenõuetekohase täitmise eest, kui selle põhjuseks olid asjaolud, mille saabumist Pooled Lepingu sõlmimisel ette ei näinud ega võinudki ette näha. Sellisteks vääramatu jõu asjaoludeks on:"));
        addParagraph(document, normalChunk("10.1.1. Üldstreik, massilised rahutused Poolte asukoha haldusüksuses; " +
                "sõda, erakorraline seisukord või eriolukord; metsatulekahju raie asukoha haldusüksuses; Riigikogu " +
                "või valitsuse akt, mis takistab oluliselt Lepingu täitmist; ilmastikutingimustest tulenevad keelud " +
                "avalikult kasutatavate teede kasutamise kohta või tööde tegemise kohta metsas (tuleoht, metsateede " +
                "sulgemine). Pooled võivad kokkuleppel lugeda vääramatu jõu asjaoludeks ka Lepingus loetlemata sündmusi."));
        addParagraph(document, normalChunk("10.2. Pool, kelle kohustuste täitmist takistab vääramatu jõu asjaolu, on kohustatud sellest viivitamatult kirjalikult teatama teisele Poolele."));
        addParagraph(document, normalChunk("10.3. Kui vääramatu jõu asjaolud kestavad kauem kui 90 päeva, loetakse Leping lõppenuks seoses täitmise võimatusega. Sellisel juhul ei ole kummalgi Poolel õigust nõuda teiselt Poolelt mittetäitmise või mittenõuetekohase täitmisega tekkinud kahjude hüvitamist."));
        addParagraph(document, boldChunk("11. Lepingu kehtivus"));
        addParagraph(document, normalChunk("11.1. Käeolev Leping jõustub allakirjutamise momendist ja kehtib kuni Lepinguliste kohustuste täitmiseni. Pooled vabanevad Lepinguliste kohustuste täitmisest käesolevas Lepingus ettenähtud juhtudel. "));
        addParagraph(document, normalChunk("11.2. Käesolevat Lepingut võib lõpetada ennetähtaegselt Poolte kirjalikul kokkuleppel. Üks Pool võib lõpetada käesolevat Lepingut ühepoolselt ennetähtaegselt käesolevas Lepingus ettenähtud juhtudel. "));

        addParagraph(document, boldChunk("12. Lepingu muutmine"));
        addParagraph(document, normalChunk("12.1. Käesolevat Lepingut saab muuta ainult Poolte kokkuleppel."));
        addParagraph(document, normalChunk("12.2. Kõik Lepingu muudatused, parandused ja täiendused peavad olema " +
                "sõlmitud kirjalikult ja allkirjastatud Poolte poolt. "));

        addParagraph(document, boldChunk("13. Vaidluste lahendamine"));
        addParagraph(document, normalChunk("13.1. Käesolevast Lepingust tulenevad vaidlused püütakse lahendada " +
                "Pooltevaheliste läbirääkimistega. Kokkuleppe mittesaavutamisel lahendatakse vaidlus kohtus, Eesti Vabariigi seadustega ette nähtud korras."));

        addParagraph(document, boldChunk("14. Muud tingimused"));
        addParagraph(document, normalChunk("14.1. Lepinguga reguleerimata küsimustes juhinduvad Pooled Eesti Vabariigis kehtivatest õigusaktidest."));
        addParagraph(document, normalChunk("14.2. Käesolevale Lepingule allakirjutamisega kinnitavad Pooled, et neil on volitus sõlmida käesolev Leping selles kindlaksmääratud tingimustel"));
        addParagraph(document, normalChunk("Käesolev Leping on sõlmitud ja alla kirjutatud kahes (2) võrdset juriidilist jõudu omavas eksemplaris, millest üks antakse Ostjale ja teine Müüjale."));
    }

    private void addCadastresTable(Document document, ContractDetails contractDetails) throws DocumentException {
        document.newPage();
        addParagraph(document, normalChunk("3.3. Müüja ja Ostja on kokku leppinud Lepingu objekti järgmistes tingimustes:"));

        PdfPTable table = new PdfPTable(6);
        table.setWidthPercentage(100);
        addCell(table, "Kinnistu");
        addCell(table, "Katastriüksuse nr");
        addCell(table, "Eraldise nr");
        addCell(table, "Raieliik");
        addCell(table, "Pindala");
        addCell(table, "Hinnanguline raiutav maht (tm)");

        for (ContractualCadastre cadastre : contractDetails.getCadastres()) {
            cadastre.getForestSections().stream().sorted(Comparator.comparing(ForestSection::getSectionNumber)).forEach(forestSection -> {
                addCell(table, cadastre.getName() == null ? "" : cadastre.getName());
                addCell(table, cadastre.getId());
                addCell(table, forestSection.getSectionNumber().toString());
                addCell(table, forestSection.getTypeOfWork());
                addCell(table, forestSection.getArea().toString());
                addCell(table, String.valueOf(forestSection.getAmountToBeCut().intValue()));
            });
        }
        document.add(table);
    }

    private void addCell(PdfPTable table, String text) {
        PdfPCell pdfPCell = new PdfPCell(new Phrase(normalChunk(text)));
        pdfPCell.setHorizontalAlignment(Element.ALIGN_CENTER);
        table.addCell(pdfPCell);
    }

    private String createCadastreString(ContractualCadastre cc) {
        return String.format("(registriosa nr %s, katastriüksuse tunnus %s) %s", cc.getRegistrationPartNumber(), cc.getId(), cc.getAddress());
    }

}
