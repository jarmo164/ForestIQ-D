package ee.metsis.contracts.pdf;

import com.itextpdf.text.Chunk;
import com.itextpdf.text.Document;
import com.itextpdf.text.DocumentException;
import ee.finenet.fineframe.exceptions.BadRequestException;
import ee.finenet.fineframe.utilities.DateUtility;
import ee.metsis.contracts.ContractData;
import ee.metsis.contracts.ContractDetails;
import ee.metsis.contracts.ContractualCadastre;
import ee.metsis.contracts.ForestSection;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

public class WithoutForrestPlanPdfCreator extends PdfCreator {
    public void doCreate(Document document, ContractData contractData) throws DocumentException {

        ContractDetails contractDetails = contractData.getContractDetails();

        addParagraph(document, boldChunk("1. Üldsätted"));

        addParagraph(document, normalChunk("1.1. Lepingu esemeks on kasvava metsa raieõiguse võõrandamine, mille tulemusena läheb Lepingu objektiks oleval " +
                "kinnistul kasvava ja raiumisele kuuluva metsa omandiõigus üle Müüjalt Ostjale."));
        addParagraph(document, normalChunk("1.2. Lepingu objektiks on Müüjale kuuluval kinnistul aadressiga "
                + createEnumerationString(contractDetails.getCadastres().stream().map(this::createCadastreString).collect(Collectors.toList())) +
                " asuva kasvava metsa raieõigus."));
        addParagraph(document, normalChunk("1.3. Ostja lisab Müüja nõudmisel Lepingule plaani, millelt nähtub raieõiguse ligikaudne ulatus. " +
                "Kui Lepingu objektiks oleval kinnistul ei ole kehtivat metsamajandamiskava, siis Ostja Lepingule plaani lisama ei pea. Pooled aktsepteerivad fakti," +
                " et plaanil märgitud eraldiste piirid võivad uue metsamajandamiskava koostamisega muutuda."));
        addParagraph(document, normalChunk("1.4. Ostja esitab Lepingu sõlmimise järgselt Müüja esindajana " +
                "Keskkonnaametile Lepingule ja vorminõuetele vastava metsateatise. Müüjal puudub õigus metsateatise " +
                "projekti kasutada ja käsutada."));
        addParagraph(document, normalChunk("1.5. Müüja annab Lepingu sõlmimisel Ostjale üle kogu Lepingu objekti " +
                "puudutava dokumentatsiooni. Lepingu objekti juhusliku hävimise ja kahjustumise riisiko läheb Ostjale " +
                "üle Lepingu objekti puudutava dokumentatsiooni üleandmisega."));

        addParagraph(document, boldChunk("2. Poolte kinnitused"));
        addParagraph(document, normalChunk("2.1 Müüjakinnitused"));
        addParagraph(document, normalChunk("2.1.1 Müüja on Lepingu objektiks oleva kasvava metsa omanik ja valdaja;"));
        addParagraph(document, normalChunk("2.1.2 Müüja ei ole Lepingu objektiks olevat raieõigust ega kinnistut võõrandanud;"));
        addParagraph(document, normalChunk("2.1.3 Lepinguobjekti suhtes puuduvad mistahes kolmandate isikute õigused ning " +
                "Lepingu objekti käsutamine ei ole piiratud ega keelatud."));

        addParagraph(document, boldChunk("2.2 Ostja kinnitused"));

        addParagraph(document, normalChunk("2.2.1 Ostja on teadlik Lepingu objektiks oleva kinnistu seisukorrast ja raieõiguse sisust ning sõlmib" +
                " Lepingu eeldusel, et Müüja poolt Ostjale edastatud informatsioon vastab tõele;"));
        addParagraph(document, normalChunk("2.2.2 Ostja on Lepingu objekti vahetult enne Lepingu sõlmimist põhjalikult üle vaadanud ja on teadlik Lepingu objekti " +
                "seisukorrast;"));
        addParagraph(document, normalChunk("2.2.3 Ostja ei soovi eraldiste piiride märkimist Müüja poolt."));

        addParagraph(document, boldChunk("3. Müügihind ja tasumise kord"));
        addParagraph(document,
                normalChunk("3.1. Kasvava metsa raieõiguse müügihind on " + formatMoney(contractDetails.getPrice()) + " eurot"));
        List<List<Chunk>> sentenceParts = contractData.getSellers().stream().map(this::createWhichSellerGetsWhatChunks).collect(Collectors.toList());
        List<Chunk> whoGetsWhatSentence = new ArrayList<>();
        whoGetsWhatSentence.add(normalChunk("3.2. Ostja tasub kasvava metsa raieõiguse võõrandamise eest Müüja "));
        whoGetsWhatSentence.addAll(createSentenceFromChunks(sentenceParts));
        addParagraph(document, whoGetsWhatSentence.toArray(new Chunk[whoGetsWhatSentence.size()]));
        if (contractData.getContractDetails().isBankDaysToPayUpCondition()) {
            addParagraph(document, normalChunk(String.format("3.3. Ostja tasub käesoleva Lepingu punktis 3.1 " +
                    "nimetatud ostuhinna hiljemalt %s pangapäeva " +
                    "jooksul peale metsateatiste allkirjastamist Keskkonnaameti poolt.", contractData.getContractDetails().getBankDaysToPayUp())));
        } else {
            addParagraph(document, normalChunk(String.format("3.3. Ostja tasub käesoleva Lepingu punktis 3.1 " +
                    "nimetatud ostuhinna hiljemalt %s pangapäeva " +
                    "jooksul peale Lepingu allkirjastamist.", contractData.getContractDetails().getBankDaysToPayUp())));
        }

        addParagraph(document, normalChunk("3.4.  Võõrandatava raieõiguse hinna arvestamise aluseks on kasvava metsa väärtus vastavalt " +
                "hinnangulistele kogustele. Metsamaterjali reaalne väljatulek või hinnanguliste koguste ületamine " +
                "ei mõjuta raieõiguse müügihinda ega metsamaterjali omandiõigust."));

        addParagraph(document, boldChunk("4. Raieõiguse sisu"));
        addParagraph(document, normalChunk(String.format("4.1. Lepingu alusel teostatav%s.  Ostja teostab " +
                "raieid vastavalt Keskkonnaameti poolt raiet lubava märkega tagastatud metsateatisele", createWorkTypeSentence(contractDetails.getCadastres()))));
        addParagraph(document, normalChunk("4.2. Raieõigus annab Ostjale õiguse langetada puid Lepingus ja metsateatisel fikseeritud ulatuses, " +
                "kohas, ajal ja tingimustel. Lisaks annab raieõigus Ostjale õiguse omandada langetatud puud, " +
                "valmistada nendest puudest puidusortimente ja saadud puidusortimendid metsast ära vedada. " +
                "Raieõiguse alusel saadud metsamaterjal kuulub reservatsioonideta raieõiguse teostanud " +
                "raieõiguse omanikule"));
        addParagraph(document, normalChunk(String.format("4.3. Ostjal on õigus teostada raieõigust kuni %s. Ostjal on õigus keskkonnaametile esitama, vastu võtma ning pikendama " +
                "metsateatist ja metsamajandamiskavasid.",
                DateUtility.estonianDate(contractDetails.getFinalDate()))));
        addParagraph(document, normalChunk(String.format("4.4. Raieõiguse teostamisel saadud puidu kohustub Ostja metsast välja vedama ja raielangi " +
                "puhastama hiljemalt %s. " +
                "Raielangi puhastamise viisiks on vallidesse kogutud raiejäätmete kõdunema jätmine ja/või " +
                "raiejäätmetega kokkuveoteede tugevdamine ja/või raiejäätmete äravedu langilt vastavalt Ostja " +
                "äranägemisele.", DateUtility.estonianDate(contractDetails.getFinalDate()))));
        addParagraph(document, normalChunk("4.5. Lepinguga kaasneb Ostja õigus kasutada Lepingu objekti maad vastavalt raieõiguse sisule. " +
                "Ostjal on õigus kasutada Müüjale kuuluvat kinnistut lisaks raieõiguse teostamisele ka raieõiguse " +
                "teostamiseks vajaliku tehnikaga liikumiseks. Nimetatud liikumine toimub eelkõige olemasolevaid " +
                "teid pidi. Kolmandate isikute maaüksusi on Ostjal õigus kasutada juhul, kui ta ise on saavutanud " +
                "maaüksuse omanikuga vastava kokkuleppe."));
        addParagraph(document, normalChunk(String.format("4.6. Ostjal on Lepingu alusel õigus ladustada metsamaterjali %s. " +
                "Metsamaterjali ei tohi ladustada õuealal. Õueala ei tohi kasutada " +
                "ka metsatehnikaga liiklemiseks", finishSentenceCadastresWithIds(contractDetails.getCadastres()))));
        addParagraph(document, normalChunk(String.format("4.7. Raiumise eritingimused: %s", Optional.ofNullable(contractDetails.getAdditionalTerms()).orElse(" ei ole."))));

        addParagraph(document, boldChunk("5. Poolte õigused ja kohustused"));
        addParagraph(document, normalChunk("5.1. Ostja kohustub kasutama Lepingu objekti heaperemehelikult. Ostja kohustub tagama metsa " +
                "jätkusuutlikkuse ja järgima metsanduse head tava ning muuhulgas tegema kõik endast " +
                "oleneva, et vältida metsa tervisliku seisundi halvenemist ja tuleohtu."));
        addParagraph(document, normalChunk("5.2. Ostja kohustub raieõiguse teostamisel rakendama tehnoloogiaid ja tehnilisi vahendeid, mis " +
                "kahjustavad kasvavat metsa, pinnast ja ümbritsevat keskkonda võimalikult vähe."));
        addParagraph(document, normalChunk("5.3. Ostja kohustub hoidma funktsionaalses korras teed, kvartalisihid, veejuhtmed ja nendele " +
                "ehitatud rajatised, kus toimub Lepingu objektiks oleva raieõiguse alusel metsavarumine ja " +
                "sellega seotud tegevus (metsamaterjali väljavedu). Metsamaterjali väljaveo käigus lõhutud " +
                "teed, truubid, sillad ja teised rajatised kohustub Ostja omal kulul parandama."));
        addParagraph(document, normalChunk("5.4. Müüja kohustub Lepingu objekti alust, kinnistut ilma Ostja eelneva kirjaliku nõusolekuta mitte " +
                "võõrandama ajal, mil Lepinguga võõrandatud raieõigus on Ostja poolt veel teostamata, v.a " +
                "juhul kui Lepingu punktis 4.3 nimetatud tähtaeg on möödunud. Lepingu objekti aluse kinnistu " +
                "võõrandamine on lubatud siis, kui Müüja tagab kõikide Lepingus kokkulepitud Müüjale " +
                "rakenduvate kohustuste ülevõtmise. Lepingu objekti aluseks oleva kinnistu omandaja poolt " +
                "koos kohustusega anda samad kohustused üle ka järgmisele omandajale."));
        addParagraph(document, normalChunk("5.5. Müüja kohustub kuni punktis 4.3 sätestatud tähtaja saabumiseni mitte teostama ega " +
                "võimaldama kolmandatel isikutel teostada raieõigust Lepingu alusel väljastatavas " +
                "metsateatises märgitud eraldistel."));
        addParagraph(document, normalChunk("5.6. Müüja kohustub mitte takistama metsamajanduskava ja/või metsateatise kinnitamist ja " +
                "raieõiguse teostamist. Raieõiguse teostamise takistamiseks loetakse muuhulgas, kuid mitte ainult " +
                "raiepiletite ja raiekava kinnitamata jätmist, ligipääsu takistamist Lepingu objektile ja " +
                "metsamaterjali väljavedamise takistamist."));

        addParagraph(document, boldChunk("6. Konfidentsiaalsuskohustus"));
        addParagraph(document, normalChunk("6.1. Käesolev Leping, selle sisu ning Lepingus täitmise käigus omandatud informatsioon on " +
                "konfidentsiaalne nii oma sisult kui ka vormilt."));
        addParagraph(document, normalChunk("6.2. Pooled kohustuvad tegema kõik endast oleneva, et käesolev Leping tervikuna, käesolevas " +
                "Lepingus sisalduvad kokkulepped või käesolevas Lepingus sisalduvate kokkulepete täitmise " +
                "käigus Poolte poolt omandatud informatsioon ei satuks kolmandate isikute valdusesse, " +
                "kasutusse ega käsutusse. Nimetatud kohustuse täitmiseks peavad Pooled kasutama kõiki " +
                "abinõusid, mis aitavad sellise kohustuse täitmisele mis tahes viisil kaasa."));
        addParagraph(document, normalChunk("6.3. . Pooled võivad konfidentsiaalset informatsiooni edastada oma töötajatele ja " +
                "lepingupartneritele, kui see on vajalik Lepinguliste kohustuste täitmiseks."));
        addParagraph(document, normalChunk("6.4. Konfidentsiaalsuskohustus kehtib tähtajatult ega sõltu käesoleva Lepingu kehtivusest."));

        addParagraph(document, boldChunk("7. Vastutus"));
        addParagraph(document, normalChunk("7.1. Lepingu alusel väljastatava metsateatise alusel raieõiguse võõrandamisel kolmandale isikule või " +
                "metsateatise kasutamisel iseenda huvides, kohustub Müüja tasuma Ostjale leppetrahvi " +
                "summas kaks tuhat (2000) eurot ja kandma Ostja poolt Lepingu objektiga seoses tehtud " +
                "kulutused."));
        addParagraph(document, normalChunk("7.2. Kui Müüja rikub konfidentsiaalsuskohustust ning tekitab sellega Ostjale kahju, siis on Ostjal " +
                "õigus nõuda leppetrahvi summas kaks tuhat eurot (2000€)."));
        addParagraph(document, normalChunk("7.3. Kui Müüja takistab metsamajanduskava ja/või raieteatise kinnitamist või raieõiguse teostamist, " +
                "siis on Ostjal õigus nõuda leppetrahvi summas kaks tuhat eurot (2000€)."));

        addParagraph(document, boldChunk("8. Lepingu muutmine ja lepingu lõppemine"));
        addParagraph(document, normalChunk("8.1. Leping kehtib kuni lepinguliste kohustuste kohase täitmiseni või kuni Lepingu punktis 4.3 " +
                "märgitud tähtaja saabumiseni."));
        addParagraph(document, normalChunk("8.2. Lepingu muutmisele või lõpetamisele suunatud avaldused ja kokkulepped peavad olema " +
                "sõlmitud kirjalikus vormis."));
        addParagraph(document, normalChunk("8.3. Pooled võivad Lepingust taganeda ainult siis, kui teine Pool on Lepingut rikkunud tahtlikult."));

        addParagraph(document, normalChunk(""));
    }

    private String finishSentenceCadastresWithIds(List<ContractualCadastre> cadastres) {
        return (cadastres.size() > 1 ? "kinnistutel katastriüksuse tunnustega " : "kinnistul katastriüksuse tunnusega ") +
                createEnumerationString(cadastres.stream().map(ContractualCadastre::getId).collect(Collectors.toList()));
    }

    private String createWorkTypeSentence(List<ContractualCadastre> cadastres) {
        List<String> workTypes = cadastres
                .stream().map(ContractualCadastre::getForestSections)
                .flatMap(fs -> fs.stream().map(ForestSection::getTypeOfWork))
                .distinct()
                .map(this::translateWorkType).collect(Collectors.toList());
        String workTypeList = createEnumerationString(workTypes);
        return workTypes.size() > 1 ? "ad raieliigid on " + workTypeList : " raieliik on " + workTypeList;
    }

    private String translateWorkType(String code) {
        if (code.equals("LR")) return "lageraie";
        if (code.equals("HR")) return "harvendusraie";
        if (code.equals("AR")) return "aegjärkne raie";
        if (code.equals("SR")) return "sanitaarraie";
        if (code.equals("VA")) return "valgustusraie";
        throw new BadRequestException("ILLEGAL_CONTRACT_INPUT_UNKNOWN_WORK_TYPE");
    }

    private String createCadastreString(ContractualCadastre cadastre) {
        return String.format("%s %s (registriosa nr %s katastriüksuse tunnus %s)", cadastre.getAddress(), cadastre.getName() != null ? ", " + cadastre.getName() : "", cadastre.getRegistrationPartNumber(), cadastre.getId());
    }
}
