package ee.metsis.contracts.autocompleters;

import ee.metsad.register.models.ForestNotificationModel;
import ee.metsis.contracts.ContactInformation;
import ee.metsis.contracts.ContractParty;
import ee.metsis.contracts.ContractualCadastre;
import ee.metsis.contracts.ForestSection;
import ee.metsis.contracts.SellerParty;
import ee.metsis.owners.OwnerNotFoundException;
import ee.metsis.owners.OwnerService;
import ee.metsis.owners.cadastres.CadastreNotFoundException;

import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.stream.Collectors;

public class AutoCompleterService {
    private final AutoCompleterDao autoCompleterDao;
    private final OwnerService ownerService;

    public AutoCompleterService(AutoCompleterDao autoCompleterDao, OwnerService ownerService) {
        this.autoCompleterDao = autoCompleterDao;
        this.ownerService = ownerService;
    }

    public List<String> getCadastresById(String id) {
        return autoCompleterDao.getCadastresById(id);
    }

    public List<String> getOwnersById(String id) {
        return autoCompleterDao.getOwnersById(id);
    }

    public ContractualCadastre getCadastreDetails(String id) {
        ownerService.findCadastre(id).orElseThrow((CadastreNotFoundException::new));
        ownerService.getMkData(id, true);
        return ownerService.findCadastre(id).map(cadastre -> {
            List<ForestNotificationModel> cadastreNotifications = ownerService.getCadastreNotifications(id, true);
            Map<Integer, ForestNotificationModel> notifications =
                    cadastreNotifications
                            .stream()
                            .filter(n -> n.getState().intValue() == 6)
                            .collect(Collectors.toMap(
                                    fnm -> fnm.getCadastreSubPartCode().intValue(),
                                    fnm -> fnm,
                                    (fnm1, fnm2) -> {
                                        if (fnm1.getRegistrationDate() > fnm2.getRegistrationDate()) {
                                            return fnm1;
                                        }
                                        return fnm2;
                                    }
                            ));
            ContractualCadastre cc = new ContractualCadastre();
            cc.setId(cadastre.getId());
            cc.setForestSections(cadastre.getCadastreSubParts().stream().map(cadastreSubPart -> {
                ForestSection forestSection = new ForestSection();
                forestSection.setArea(cadastreSubPart.getArea());
                forestSection.setSectionNumber(cadastreSubPart.getSubPartCode());
                Optional<ForestNotificationModel> notification = Optional.ofNullable(notifications.get(cadastreSubPart.getSubPartCode()));
                forestSection.setTypeOfWork(notification.map(ForestNotificationModel::getWorkCode).orElse("LR"));
                forestSection.setAmountToBeCut(notification.map(ForestNotificationModel::getAmountToBeCut).orElse(0.0));
                forestSection.setNotificationId(notification.map(cn -> cn.getNotificationNumber().toString()).orElse(null));
                return forestSection;
            }).collect(Collectors.toList()));
            cc.setAddress(cadastre.getAddress());
            cc.setName(cadastre.getName());
            cc.setRegistrationPartNumber(cadastre.getRegNr());
            return cc;
        }).orElseThrow((CadastreNotFoundException::new));
    }

    public ContractParty getOwnersDetails(String id) {
        ownerService.findOwner(id).orElseThrow(OwnerNotFoundException::new);
        return ownerService.findOwner(id).map(owner -> {
            ContractParty contractParty = new SellerParty();
            contractParty.setCode(owner.getId());
            contractParty.setName(owner.getName());
            ContactInformation ci = new ContactInformation();
            ci.setAddress(owner.getAddress());
            ci.setEmail(owner.getEmail());
            ci.setPhoneNo(owner.getPhone());
            contractParty.setContactInformation(ci);
            return contractParty;
        }).orElseThrow(OwnerNotFoundException::new);
    }
}
