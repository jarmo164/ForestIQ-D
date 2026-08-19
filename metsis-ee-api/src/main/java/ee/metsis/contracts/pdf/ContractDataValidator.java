package ee.metsis.contracts.pdf;

import ee.finenet.fineframe.exceptions.BadRequestException;
import ee.finenet.fineframe.utilities.StringUtility;
import ee.metsis.contracts.BuyerParty;
import ee.metsis.contracts.ContactInformation;
import ee.metsis.contracts.ContractData;
import ee.metsis.contracts.ContractDetails;
import ee.metsis.contracts.ContractPartyProxy;
import ee.metsis.contracts.ContractualCadastre;
import ee.metsis.contracts.ForestSection;
import ee.metsis.contracts.SellerParty;

import java.util.List;
import java.util.Optional;

public class ContractDataValidator {
    public static void validate(ContractData contractData) {
        if (contractData.getTemplateNumber() != 0 && contractData.getTemplateNumber() != 1) {
            throw new BadRequestException("ILLEGAL_CONTRACT_INVALID_TEMPLATE_NUMBER");
        }
        if (StringUtility.isNullOrBlank(contractData.getContractNumber())) {
            throw new BadRequestException("ILLEGAL_CONTRACT_CONTRACT_NR_MISSING");
        }

        BuyerParty buyer = contractData.getBuyer();
        if (StringUtility.isNullOrBlank(buyer.getCode())) {
            throw new BadRequestException("ILLEGAL_CONTRACT_BUYER_CODE_MISSING");
        }
        if (StringUtility.isNullOrBlank(buyer.getName())) {
            throw new BadRequestException("ILLEGAL_CONTRACT_BUYER_NAME_MISSING");
        }
        ContactInformation buyerContacts = buyer.getContactInformation();
        if (StringUtility.isNullOrBlank(buyerContacts.getAddress())) {
            throw new BadRequestException("ILLEGAL_CONTRACT_BUYER_ADDRESS_IS_MISSING");
        }

        ContractDetails details = contractData.getContractDetails();
        if (details.getPrice() <= 0) {
            throw new BadRequestException("ILLEGAL_CONTRACT_PRICE_MUST_BE_POSITIVE");
        }
        if (details.getDateOfEnforcement() == null) {
            throw new BadRequestException("ILLEGAL_CONTRACT_DATE_OF_ENFORCEMENT_MISSING");
        }
        if (details.getFinalDate() == null) {
            throw new BadRequestException("ILLEGAL_CONTRACT_FINAL_DATE_MISSING");
        }
        if (details.getDateOfEnforcement().after(details.getFinalDate())) {
            throw new BadRequestException("ILLEGAL_CONTRACT_FINAL_DATE_BEFORE_DATE_OF_ENFORCEMENT");
        }
        if (details.getBankDaysToPayUp() == null || details.getBankDaysToPayUp() <= 0) {
            throw new BadRequestException("ILLEGAL_CONTRACT_BANK_DAYS_TO_PAY_UP_MUST_BE_POSITIVE");
        }
        if (StringUtility.isNullOrBlank(details.getWrittenPrice())) {
            throw new BadRequestException("ILLEGAL_CONTRACT_WRITTEN_PRICE_MISSING");
        }
        List<ContractualCadastre> cadastres = details.getCadastres();

        if (cadastres.isEmpty()) {
            throw new BadRequestException("ILLEGAL_CONTRACT_CADASTRES_EMPTY");
        }
        for (ContractualCadastre cadastre : cadastres) {
            if (StringUtility.isNullOrBlank(cadastre.getId())) {
                throw new BadRequestException("ILLEGAL_CONTRACT_CADASTRE_ID_MISSING");
            }
            if (StringUtility.isNullOrBlank(cadastre.getAddress())) {
                throw new BadRequestException("ILLEGAL_CONTRACT_CADASTRE_ADDRESS_MISSING");
            }
            List<ForestSection> forestSections = cadastre.getForestSections();
            if (forestSections.size() < 1) {
                throw new BadRequestException("ILLEGAL_CONTRACT_NO_FOREST_SECTIONS");
            }

            if (contractData.getTemplateNumber() == ContractData.TEMPLATE1) {
                for (ForestSection forestSection : forestSections) {
                    if (forestSection.getSectionNumber() == null) {
                        throw new BadRequestException("ILLEGAL_CONTRACT_FOREST_SECTION_ID_MISSING");
                    }
                    if (StringUtility.isNullOrBlank(forestSection.getTypeOfWork())) {
                        throw new BadRequestException("ILLEGAL_CONTRACT_FOREST_SECTION_TYPE_OF_WORK_MISSING");
                    }
                }
            }
        }

        ContractPartyProxy buyerProxy = buyer.getProxy();
        if (buyerProxy != null) {
            if (StringUtility.isNullOrBlank(buyerProxy.getCode())) {
                throw new BadRequestException("ILLEGAL_CONTRACT_BUYER_PROXY_CODE_IS_MISSING");
            }
            if (StringUtility.isNullOrBlank(buyerProxy.getName())) {
                throw new BadRequestException("ILLEGAL_CONTRACT_BUYER_PROXY_NAME_IS_MISSING");
            }
        }

        List<SellerParty> sellers = contractData.getSellers();
        if (sellers.isEmpty()) {
            throw new BadRequestException("ILLEGAL_CONTRACT_NO_SELLERS");
        }
        for (SellerParty seller : sellers) {
            if (StringUtility.isNullOrBlank(seller.getCode())) {
                throw new BadRequestException("ILLEGAL_CONTRACT_SELLER_CODE_MISSING");
            }
            if (StringUtility.isNullOrBlank(seller.getName())) {
                throw new BadRequestException("ILLEGAL_CONTRACT_SELLER_NAME_MISSING");
            }
            if (StringUtility.isNullOrBlank(seller.getBankAccountNumber())) {
                throw new BadRequestException("ILLEGAL_CONTRACT_SELLER_BANK_ACCOUNT_NR_IS_MISSING");
            }
            if (seller.getMoneyObtainedFromTheDeal() == null) {
                throw new BadRequestException("ILLEGAL_CONTRACT_SELLER_MONEY_OBTAINED_FROM_THE_DEAL_MISSING");
            }

        }
        Optional<SellerParty> sellerWithPhoneNo = sellers.stream()
                .filter(s -> s.getContactInformation().getPhoneNo() != null)
                .findFirst();
        if (!sellerWithPhoneNo.isPresent()) {
            throw new BadRequestException("ILLEGAL_CONTRACT_INPUT_NO_SELLER_HAS_PHONE_NO");
        }
    }
}
