package ee.metsis.contracts;

import ee.finenet.fineframe.configuration.NoValidaton;
import ee.finenet.fineframe.configuration.PropertyReadingInstruction;
import ee.finenet.fineframe.configuration.StringReadingInstruction;
import ee.finenet.fineframe.configuration.instructions.IntegerReadingInstruction;
import ee.finenet.fineframe.configuration.validators.NotNullValidator;

import java.util.Properties;

public class BuyerConfiguration {

    private final BuyerParty buyerParty;
    private final String defaultAdditionalTerms;
    private final Integer daysToPayUp;

    public BuyerConfiguration(Properties properties) {
        String buyerCode = new PropertyReadingInstruction<>(
                properties,
                "METSIS_BUYER_CODE",
                NotNullValidator.INSTANCE,
                StringReadingInstruction.INSTANCE
        ).read();
        String buyerName = new PropertyReadingInstruction<>(
                properties,
                "METSIS_BUYER_NAME",
                NotNullValidator.INSTANCE,
                StringReadingInstruction.INSTANCE
        ).read();
        String buyerAddress = new PropertyReadingInstruction<>(
                properties,
                "METSIS_BUYER_ADDRESS",
                NotNullValidator.INSTANCE,
                StringReadingInstruction.INSTANCE
        ).read();
        String buyerEmail = new PropertyReadingInstruction<>(
                properties,
                "METSIS_BUYER_MAIL",
                NoValidaton.INSTANCE,
                StringReadingInstruction.INSTANCE
        ).read();
        String buyerPhone = new PropertyReadingInstruction<>(
                properties,
                "METSIS_BUYER_PHONE",
                NoValidaton.INSTANCE,
                StringReadingInstruction.INSTANCE
        ).read();
        String buyerProxyCode = new PropertyReadingInstruction<>(
                properties,
                "METSIS_BUYER_PROXY_CODE",
                NotNullValidator.INSTANCE,
                StringReadingInstruction.INSTANCE
        ).read();
        String buyerProxyName = new PropertyReadingInstruction<>(
                properties,
                "METSIS_BUYER_PROXY_NAME",
                NotNullValidator.INSTANCE,
                StringReadingInstruction.INSTANCE
        ).read();
        String buyerProxyPhone = new PropertyReadingInstruction<>(
                properties,
                "METSIS_BUYER_PROXY_PHONE",
                NoValidaton.INSTANCE,
                StringReadingInstruction.INSTANCE
        ).read();
        String buyerProxyMail = new PropertyReadingInstruction<>(
                properties,
                "METSIS_BUYER_PROXY_MAIL",
                NoValidaton.INSTANCE,
                StringReadingInstruction.INSTANCE
        ).read();
        String buyerProxyAddress = new PropertyReadingInstruction<>(
                properties,
                "METSIS_BUYER_PROXY_ADDRESS",
                NoValidaton.INSTANCE,
                StringReadingInstruction.INSTANCE
        ).read();
        Integer daysToPayUp = new PropertyReadingInstruction<>(
                properties,
                "METSIS_BUYER_DAYS_TO_PAY_UP",
                NotNullValidator.INSTANCE,
                IntegerReadingInstruction.INSTANCE
        ).read();
        this.defaultAdditionalTerms = new PropertyReadingInstruction<>(
                properties,
                "METSIS_CONTRACT_DEFAULT_ADDITIONAL_TERMS",
                NoValidaton.INSTANCE,
                StringReadingInstruction.INSTANCE
        ).read();
        this.daysToPayUp = daysToPayUp;
        this.buyerParty = new BuyerParty();
        buyerParty.setCode(buyerCode);
        buyerParty.setName(buyerName);
        ContactInformation buyerContacts = new ContactInformation();
        buyerContacts.setAddress(buyerAddress);
        buyerContacts.setEmail(buyerEmail);
        buyerContacts.setPhoneNo(buyerPhone);
        buyerParty.setContactInformation(buyerContacts);
        ContractPartyProxy proxy = new ContractPartyProxy();
        proxy.setCode(buyerProxyCode);
        proxy.setName(buyerProxyName);
        ContactInformation buyerProxyContacts = new ContactInformation();
        buyerProxyContacts.setAddress(buyerProxyAddress);
        buyerProxyContacts.setEmail(buyerProxyMail);
        buyerProxyContacts.setPhoneNo(buyerProxyPhone);
        proxy.setContactInformation(buyerProxyContacts);
        buyerParty.setProxy(proxy);
    }

    public BuyerParty getBuyerParty() {
        return this.buyerParty;
    }

    public String getDefaultAdditionalTerms() {
        return defaultAdditionalTerms;
    }

    public Integer getDaysToPayUp() {
        return daysToPayUp;
    }
}
