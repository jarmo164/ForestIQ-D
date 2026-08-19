package ee.metsis.admin.ownerstatusadministration;

import ee.finenet.fineframe.exceptions.BadRequestException;
import ee.finenet.fineframe.utilities.StringUtility;
import ee.metsis.owners.OwnerDAO;
import ee.metsis.owners.OwnerMinimal;
import ee.metsis.owners.workdesk.ownerstatus.OwnerStatus;

import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

public class OwnerStatusService {
    private final OwnerStatusDao ownerStatusDao;
    private final OwnerDAO ownerDao;

    public OwnerStatusService(OwnerStatusDao ownerStatusDao, OwnerDAO ownerDao) {
        this.ownerStatusDao = ownerStatusDao;
        this.ownerDao = ownerDao;
    }

    public List<OwnerStatus> getPossibleOwnerStatuses() {
        return ownerStatusDao.getOwnerStatuses();
    }

    public List<String> getPossibleOwnerStatusIds() {
        return getPossibleOwnerStatuses().stream().map(OwnerStatus::getId).collect(Collectors.toList());
    }

    public void saveOwnerStatus(OwnerStatus ownerStatus) {
        if (ownerStatus == null) {
            throw new BadRequestException("OWNER_STATUS_SAVE_NO_MODEL");
        }
        if (ownerStatus.getColorHex() == null) {
            throw new BadRequestException("OWNER_STATUS_SAVE_NO_COLOR");
        }
        String colorHex = ownerStatus.getColorHex().trim();
        int colorLen = colorHex.length();
        if (colorLen < 6 || colorLen > 6 || !colorHex.matches("^[0-9A-Fa-f]+$")) {
            throw new BadRequestException("OWNER_STATUS_SAVE_INVALID_COLOR");
        }
        if (ownerStatus.getDurationDays() < 0 || ownerStatus.getDurationDays() > 50000) {
            throw new BadRequestException("OWNER_STATUS_SAVE_INVALID_DURATION_DAYS");
        }
        String ownerStatusId = StringUtility.trimToEmpty(ownerStatus.getId());
        if (ownerStatusId.isEmpty() || ownerStatusId.length() > 100) {
            throw new BadRequestException("OWNER_STATUS_SAVE_INVALID_ID");
        }
        ownerStatus.setId(ownerStatusId);
        Optional<OwnerStatus> ownerStatusById = ownerDao.getOwnerStatusById(ownerStatusId);
        if (ownerStatusById.isPresent()) {
            ownerStatusDao.updateOwnerStatus(ownerStatus);
        } else {
            ownerStatusDao.createOwnerStatus(ownerStatus);
        }
    }

    public void deleteOwnerStatus(String id) {
        List<OwnerMinimal> ownersWithGivenStatus = ownerDao.searchOwnersByStatus(id);
        if (!ownersWithGivenStatus.isEmpty()) {
            throw new BadRequestException("OWNERS_EXIST_WITH_GIVEN_STATUS");
        }
        boolean protectedStatus = ownerDao.getOwnerStatusById(id).map(OwnerStatus::isProtectedReason).orElse(false);
        if (protectedStatus) {
            throw new BadRequestException("CAN_NOT_DELETE_PROTECTED_STATUS");
        }
        ownerStatusDao.deleteOwnerStatus(id);
    }
}
