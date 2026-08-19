package ee.metsis.contracts;

import ee.finenet.fineframe.exceptions.BadRequestException;
import ee.finenet.fineframe.exceptions.ResourceNotFoundException;
import ee.metsis.contracts.pdf.ContractInput;
import ee.metsis.contracts.pdf.PdfCreator;
import ee.metsis.contracts.pdf.TemplateBasedDocumentCreator;
import ee.metsis.contracts.pdf.WithForrestPlanPdfCreator;
import ee.metsis.contracts.pdf.WithoutForrestPlanPdfCreator;

import java.util.List;
import java.util.Optional;

public class ContractService {
    private final ContractDao contractDao;

    private final PdfCreator withForrestPlanPdfCreator = new WithForrestPlanPdfCreator();
    private final PdfCreator withoutForrestPlanPdfCreator = new WithoutForrestPlanPdfCreator();
    private final TemplateBasedDocumentCreator templateBasedDocumentCreator;

    public ContractService(ContractDao contractDao, TemplateBasedDocumentCreator templateBasedDocumentCreator) {
        this.contractDao = contractDao;
        this.templateBasedDocumentCreator = templateBasedDocumentCreator;
    }

    public ContractIds generate(ContractData contractData) {
        String buyerCode = contractData.getBuyer().getCode();
        TemplateSpecificsForBuyer templateSpecificsForBuyer = loadBuyerTemplateStuff(buyerCode);
        byte[] contract = createContract(contractData, templateSpecificsForBuyer);
        String baseId = contractDao.saveContractBase(contractData);
        return contractDao.saveContract(contract, baseId);
    }

    private TemplateSpecificsForBuyer loadBuyerTemplateStuff(String buyerCode) {
        String logoFile = "contract-template-extras/" + buyerCode + "-logo.png";
        String footerFile = "contract-template-extras/" + buyerCode + "-footer.txt";
        try {
            byte[] logoBytes = Thread.currentThread().getContextClassLoader().getResourceAsStream(logoFile).readAllBytes();
            String footer = new String(Thread.currentThread().getContextClassLoader().getResourceAsStream(footerFile).readAllBytes());
            TemplateSpecificsForBuyer t = new TemplateSpecificsForBuyer();
            t.setHeaderLogo(logoBytes);
            t.setFooterText(footer);
            return t;
        } catch (Exception e) {
            return new TemplateSpecificsForBuyer();
        }
    }

    private byte[] createContract(ContractData contractData, TemplateSpecificsForBuyer templateSpecificsForBuyer) {
        if ("10828349".equals(contractData.getBuyer().getCode())) {
            ContractInput contract = new ContractInput(contractData);
            if (contractData.getTemplateNumber() == ContractData.TEMPLATE1) {
                return templateBasedDocumentCreator.createPdf(contract);
            }
            return templateBasedDocumentCreator.createWord(contract);
        }
        int templateNumber = contractData.getTemplateNumber();
        if (templateNumber == ContractData.TEMPLATE1) {
            return withForrestPlanPdfCreator.create(contractData, templateSpecificsForBuyer);
        } else if (templateNumber == ContractData.TEMPLATE2) {
            return withoutForrestPlanPdfCreator.create(contractData, templateSpecificsForBuyer);
        } else {
            throw new BadRequestException("ILLEGAL_CONTRACT_INVALID_TEMPLATE_NUMBER");
        }
    }

    public byte[] getCreatedContract(String id) {
        byte[] contract = contractDao.getContractById(id);
        if (contract == null) {
            throw new ResourceNotFoundException("CONTRACT_NOT_FOUND");
        }
        return contract;
    }


    public void deleteExpiredDownloads() {
        contractDao.deleteExpiredDownloads();
    }

    public Optional<ContractData> loadBaseContract(String baseContractId) {
        return contractDao.getHistoricalContractData(baseContractId);
    }

    public List<HistoricalContractInfo> getHistory(HistoricalContractSearchFilter filter) {
        return contractDao.getHistory(filter);
    }

    public void deleteContract(String id) {
        contractDao.deleteContract(id);
    }

    public Optional<ContractData> getContractBase(String baseId) {
        return contractDao.getHistoricalContractData(baseId);
    }
}
