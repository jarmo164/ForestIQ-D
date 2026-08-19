package ee.metsis.owners;

import ee.finenet.fineframe.exceptions.BadRequestException;
import ee.finenet.fineframe.exceptions.ResourceNotFoundException;
import ee.finenet.fineframe.user.UserMinimal;
import ee.finenet.fineframe.user.UserService;
import ee.finenet.fineframe.utilities.StringUtility;
import ee.maaamet.geoportaal.xgis.GeoDetails;
import ee.maaamet.geoportaal.xgis.MaaametGeoportaalService;
import ee.metsad.register.models.ForestNotificationModel;
import ee.metsad.register.services.ForestRegistryService;
import ee.metsis.admin.ownerstatusadministration.OwnerStatusService;
import ee.metsis.adminworkdesk.AdminWorkdeskPreparationData;
import ee.metsis.adminworkdesk.AdminWorkdeskSearchRequest;
import ee.metsis.adminworkdesk.AssignWorkModel;
import ee.metsis.messages.MessagesService;
import ee.metsis.owners.cadastres.Areas;
import ee.metsis.owners.cadastres.Cadastre;
import ee.metsis.owners.cadastres.CadastreNotFoundException;
import ee.metsis.owners.cadastres.cadastrelabels.CadastreLabel;
import ee.metsis.owners.cadastres.cadastrelabels.CadastreLabelsModel;
import ee.metsis.owners.cadastres.mk.ForestPlan;
import ee.metsis.owners.cadastres.mk.ForestPlanMapper;
import ee.metsis.owners.cadastres.registryfeatures.ForestRegistryFeature;
import ee.metsis.owners.logservice.LogMessage;
import ee.metsis.owners.logservice.OwnerLogService;
import ee.metsis.owners.workdesk.OwnerStatusData;
import ee.metsis.owners.workdesk.cadastreevaluation.CadastreEvaluation;
import ee.metsis.pria.CadastrePolygon;
import ee.metsis.pria.CadastrePolygonService;
import ee.metsis.users.UserDAO;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.stream.Collectors;

public class OwnerService {

    private static final Logger logger = LoggerFactory.getLogger(OwnerService.class);

    private final OwnerDAO ownerDao;
    private final UserDAO userDao;
    private final OwnerStatusService ownerStatusService;
    private final OwnerLogService ownerLogService;
    private final UserService userService;
    private final MaaametGeoportaalService geoDetailsService;
    private final CadastrePolygonService cadastrePolygonService;
    private final MessagesService messagesService;
    private final ForestRegistryService forestRegistryService;
    private final ForestPlanMapper forestPlanMapper = new ForestPlanMapper();

    private final ExecutorService executorService = Executors.newFixedThreadPool(10);

    public OwnerService(
            OwnerDAO ownerDao,
            UserDAO userDao,
            OwnerStatusService ownerStatusService,
            OwnerLogService ownerLogService,
            UserService userService,
            MaaametGeoportaalService geoDetailsService,
            CadastrePolygonService cadastrePolygonService,
            MessagesService messagesService,
            ForestRegistryService forestRegistryService) {
        this.ownerDao = ownerDao;
        this.userDao = userDao;
        this.ownerStatusService = ownerStatusService;
        this.ownerLogService = ownerLogService;
        this.userService = userService;
        this.geoDetailsService = geoDetailsService;
        this.cadastrePolygonService = cadastrePolygonService;
        this.messagesService = messagesService;
        this.forestRegistryService = forestRegistryService;
    }

    public List<OwnerMinimal> searchOwners(OwnerSearchCriteria criteria) {
        return ownerDao.searchOwners(criteria);
    }

    public Optional<Owner> findOwner(String id) {
        return ownerDao.findOwner(id);
    }

    void saveOwnerChanges(Owner owner) {
        ownerDao.saveOwnerChanges(owner);
    }

    public void sendMessageToEachOwnerFollowerExcept(String ownerId, String messageText, String except,
                                                     String sender) {
        doAsync(() -> getOwnerFollowings(ownerId).stream()
                .filter(following -> !following.equals(except))
                .forEach(following -> this.messagesService.sendMessage(messageText, sender, following)));
    }

    public Optional<Cadastre> findCadastre(String id) {
        return ownerDao.findCadastre(id);
    }

    public List<OwnerMinimal> searchOwnersForAdminWorkdesk(AdminWorkdeskSearchRequest criteria) {
        return ownerDao.searchOwnersForAdminWorkdesk(criteria);
    }

    public AdminWorkdeskPreparationData getAdminWorkdeskPreparationData() {
        return new AdminWorkdeskPreparationData(
                ownerDao.getDistinctCounties(),
                ownerDao.getDistinctMunicipalities(),
                userDao.getDistinctUserMinimals(),
                ownerDao.getDistinctOwnerTypes(),
                ownerStatusService.getPossibleOwnerStatusIds()
        );
    }

    public void assignWorkToCaller(AssignWorkModel assignWorkModel, String loggedInUsersId) {
        List<String> owners = assignWorkModel.getOwners();
        String assigneeId = assignWorkModel.getAssignee();
        ownerDao.setCallerForOwners(assigneeId, owners);
        if (!assignWorkModel.isReassign()) {
            setOwnerStatusesToAssigned(assignWorkModel, loggedInUsersId, owners);
        } else {
            setOwnerStatusesToAssigned(assignWorkModel, loggedInUsersId, owners);
            ownerLogService.writeLogAsync(assignWorkModel.getOwners().stream().map(ownerId -> buildReassignLogMessage(loggedInUsersId, assigneeId, ownerId)));
        }
        doAsync(() -> owners.forEach(owner -> addFollowing(assigneeId, owner)));
        if (owners.size() == 1) {
            String ownerId = owners.get(0);
            String ownerName = findOwner(ownerId).map(OwnerMinimal::getName).orElse("");
            messagesService.sendMessage("Owner " + ownerName + " (" + ownerId + ") has been assigned to " + assigneeId,
                    loggedInUsersId,
                    assigneeId);
        } else {
            messagesService.sendMessage("New owners have been assigned to " + assigneeId, loggedInUsersId, assigneeId);
        }
    }

    private void doAsync(Runnable runnable) {
        executorService.execute(() -> {
            try {
                runnable.run();
            } catch (Exception e) {
                logger.error("Exception with async procedure", e);
            }
        });
    }

    private void setOwnerStatusesToAssigned(AssignWorkModel assignWorkModel, String loggedInUsersId, List<String> owners) {
        String status = "ASSIGNED";
        ownerDao.setStatusForOwners(status, owners);
        ownerLogService.writeLogAsync(assignWorkModel.getOwners().stream().map(ownerId -> {
            LogMessage logMessage = new LogMessage();
            logMessage.setOwner(ownerId);
            logMessage.setCreator(loggedInUsersId);
            logMessage.setMessage(String.format("New status: %s", status));
            return logMessage;
        }));
    }

    public void setOwnerStatus(String ownerId, String newStatus, String comment, String loggedInUsersId, String assignee) {
        Owner owner = ownerDao.findOwner(ownerId).orElseThrow(() -> new ResourceNotFoundException("OWNER_NOT_FOUND"));
        ownerDao.setStatusForOwners(newStatus, Collections.singletonList(ownerId));
        LogMessage logMessage = new LogMessage();
        logMessage.setOwner(ownerId);
        logMessage.setCreator(loggedInUsersId);
        logMessage.setMessage(String.format("New status: %s" + (comment == null || comment.isEmpty() ? "%s" : "\nComment:\n%s"), newStatus, StringUtility.emptyIfNull(comment)));
        logMessage.setOwnersAssignee(assignee);
        ownerLogService.writeLog(logMessage);
        sendMessageToEachOwnerFollowerExcept(ownerId, "Owner " + owner.getName() + " (" + owner.getId() + ") " +
                "status changed to " + newStatus + ". " +
                "Comment: " + StringUtility.emptyIfNull(comment), loggedInUsersId, loggedInUsersId);
    }

    public Optional<CadastreEvaluation> getCadastreEvaluation(String cadastreNo) {
        return ownerDao.getCadastreEvaluation(cadastreNo);
    }

    public void saveCadastreEvaluation(String cadastreId, CadastreEvaluation evaluation, String loggedInUsersId) {
        ownerDao.saveEvaluation(cadastreId, evaluation);
        ownerDao.findCadastre(cadastreId).ifPresent(cadastre -> ownerLogService.writeLogAsync(cadastre.getOwners().stream().map(o -> {
            LogMessage logMessage = new LogMessage();
            logMessage.setOwner(o.getId());
            logMessage.setCreator(loggedInUsersId);
            logMessage.setMessage(String.format("Cadastre '%s' evaluation saved.\nOur price: %s\nOwner price: %s", cadastreId, evaluation.getOurPrice(), evaluation.getOwnerPrice()));
            logMessage.setOwnersAssignee(o.getAssignee().getId());

            sendMessageToEachOwnerFollowerExcept(o.getId(), String.format("Cadastre '%s' evaluated.\nOur price: " +
                            "%s\nOwner price: %s", cadastreId, evaluation.getOurPrice(), evaluation.getOwnerPrice()),
                    loggedInUsersId, loggedInUsersId);

            return logMessage;
        })));

    }

    public void markInterestingCadastres(String ownerId, List<String> cadastreIds) {
        ownerDao.deleteCadastreMarkingsForOwner(ownerId);
        ownerDao.markCadastresForOwner(ownerId, cadastreIds);
    }

    public List<OwnerMinimal> getOwnersInNeedOfEvaluation() {
        return ownerDao.searchOwnersByStatus("WAITS_FOR_EVALUATION");
    }

    public OwnerStatusData getOwnerStatusData(String ownerId) {
        Owner owner = ownerDao.findOwner(ownerId).orElseThrow(OwnerNotFoundException::new);
        List<UserMinimal> allPossibleUsers = userService.getAllUsers().stream().map(u -> new UserMinimal(u.getId(), u.getName())).collect(Collectors.toList());
        String status = owner.getStatus();
        UserMinimal assignee = owner.getAssignee();
        OwnerStatusData ownerStatusData = new OwnerStatusData();
        ownerStatusData.setAssignee(assignee);
        ownerStatusData.setPossibleAssignees(allPossibleUsers);
        ownerStatusData.setStatus(status == null ? null : ownerDao.getOwnerStatusById(status).orElseThrow(() -> new ResourceNotFoundException("NO_SUCH_OWNER_STATUS")));
        ownerStatusData.setPossibleOwnerStatuses(ownerStatusService.getPossibleOwnerStatusIds());
        return ownerStatusData;
    }

    private LogMessage buildReassignLogMessage(String loggedInUsersId, String toAssignee, String ownerId) {
        LogMessage logMessage = new LogMessage();
        logMessage.setOwner(ownerId);
        logMessage.setCreator(loggedInUsersId);
        logMessage.setMessage(String.format("Owner assigned to user '%s'", toAssignee));
        return logMessage;
    }

    public CadastreLabelsModel getCadastreLabels(String cadastreId) {
        Cadastre cadastre = ownerDao.findCadastre(cadastreId).orElseThrow(CadastreNotFoundException::new);
        List<CadastreLabel> setLabels = cadastre.getLabels();
        List<CadastreLabel> notSetLabels = new ArrayList<>(Arrays.asList(CadastreLabel.values()));
        notSetLabels.removeAll(setLabels);
        CadastreLabelsModel cadastreLabelsModel = new CadastreLabelsModel();
        cadastreLabelsModel.setSetLabels(setLabels);
        cadastreLabelsModel.setNotSetLabels(notSetLabels);
        return cadastreLabelsModel;
    }

    public void addCadastreLabel(String cadastreId, CadastreLabel label, String loggedInUsersId) {
        Cadastre cadastre = ownerDao.findCadastre(cadastreId).orElseThrow(CadastreNotFoundException::new);
        if (label == null) {
            throw new BadRequestException("UNKNOWN_CADASTRE_LABEL");
        }
        if (cadastre.getLabels().contains(label)) {
            throw new BadRequestException("CANT_DOUBLE_ASSIGN_CADASTRE_LABEL");
        }
        ownerDao.addLabelToCadastre(cadastreId, label);
        ownerLogService.writeLogAsync(cadastre.getOwners().stream().map(o -> {
            LogMessage logMessage = new LogMessage();
            logMessage.setOwner(o.getId());
            logMessage.setCreator(loggedInUsersId);
            logMessage.setMessage(String.format("Added label '%s' to cadastre '%s'.", label, cadastreId));
            logMessage.setOwnersAssignee(o.getAssignee().getId());
            sendMessageToEachOwnerFollowerExcept(o.getId(), String.format("Added label '%s' to cadastre '%s'.", label, cadastreId),
                    loggedInUsersId, loggedInUsersId);
            return logMessage;
        }));
    }

    public void removeCadastreLabel(String cadastreId, CadastreLabel label, String loggedInUsersId) {
        Cadastre cadastre = ownerDao.findCadastre(cadastreId).orElseThrow(CadastreNotFoundException::new);
        if (label == null) {
            throw new BadRequestException("UNKNOWN_CADASTRE_LABEL");
        }
        ownerDao.removeLabelFromCadastre(cadastreId, label);
        ownerLogService.writeLogAsync(cadastre.getOwners().stream().map(o -> {
            LogMessage logMessage = new LogMessage();
            logMessage.setOwner(o.getId());
            logMessage.setCreator(loggedInUsersId);
            logMessage.setMessage(String.format("Removed label '%s' from cadastre '%s'.", label, cadastreId));
            logMessage.setOwnersAssignee(o.getAssignee().getId());

            sendMessageToEachOwnerFollowerExcept(o.getId(), String.format("Removed label '%s' from cadastre '%s'.", label, cadastreId),
                    loggedInUsersId, loggedInUsersId);

            return logMessage;
        }));
    }

    public ForestPlan getMkData(String cadastre, boolean refreshCashes) {
        Optional<ForestPlan> cachedMkData = ownerDao.getMkData(cadastre);
        if (!cachedMkData.isPresent() || refreshCashes) {
            ForestPlan freshForestPlan = getEraldisPolygonsByCadastre(cadastre);
            if (freshForestPlan == null) {
                return cachedMkData.orElse(null);
            }
            ownerDao.insertMkData(freshForestPlan);
            return freshForestPlan;
        }
        return cachedMkData.get();
    }

    private ForestPlan getEraldisPolygonsByCadastre(String cadastre) {
        try {
            logger.info("Refreshing MK polygons for cadastre {}", cadastre);
            return forestRegistryService.getCadastrePolygonDetails(cadastre).map(d -> forestPlanMapper.map(d, cadastre)).orElseGet(ForestPlan::new);
        } catch (Exception e) {
            logger.error("Fetching MK data from external sources failed", e);
            return ownerDao.getMkData(cadastre).orElse(null);
        }
    }

    public Areas getCadastreAreas(String cadastre, boolean refreshCaches) {
        Optional<Areas> areas = ownerDao.getCadastreAreas(cadastre);
        if (!areas.isPresent() || refreshCaches) {
            GeoDetails geoDetails = fetchCadatreGeoDetails(cadastre);
            if (geoDetails == null) {
                return areas.orElse(new Areas());
            }
            Areas freshAreas = tranformGeodetailsToAreas(geoDetails);
            ownerDao.updateCadastreAreas(cadastre, freshAreas);
            ownerDao.updateGeoDetails(cadastre, geoDetails);
            return freshAreas;
        }
        return areas.orElse(new Areas());
    }

    private GeoDetails fetchCadatreGeoDetails(String cadastre) {
        try {
            logger.info("Refreshing cadastre {} details from geoportaal", cadastre);
            return geoDetailsService.getDetailedInfo(cadastre);
        } catch (Exception e) {
            logger.error("Fetching MK data from external sources failed", e);
            return null;
        }
    }

    private Areas tranformGeodetailsToAreas(GeoDetails geoDetails) {
        Areas areas = new Areas();
        areas.setArea(geoDetails.getPindala());
        areas.setArableArea(geoDetails.getHaritavMaa());
        areas.setBuildingsArea(geoDetails.getEhitisteAluneMaa());
        areas.setForestArea(geoDetails.getMetsamaa());
        areas.setMeadowArea(geoDetails.getRohumaa());
        areas.setOtherArea(geoDetails.getMuuMaa());
        areas.setUnderWaterArea(geoDetails.getVeeAluneMaa());
        areas.setYardArea(geoDetails.getOuemaa());
        return areas;
    }

    public void registerUnknownAddedOwnings(List<String> addedOwnings) {
        for (String cadastre : addedOwnings) {
            if (!ownerDao.cadastreExists(cadastre)) {
                try {
                    logger.info("Registering new cadastre {}", cadastre);
                    CadastrePolygon cadastrePolygon = cadastrePolygonService.getPolygonForCadastre(cadastre);
                    GeoDetails detailedInfo = geoDetailsService.getDetailedInfo(cadastre);
                    ownerDao.insertCadastre(cadastre, cadastrePolygon, detailedInfo);
                    ownerDao.updateCadastreAreas(cadastre, tranformGeodetailsToAreas(detailedInfo));
                } catch (Exception e) {
                    logger.error("Failed to insert unknown cadastre", e);
                }
            }
        }
    }

    public void updateOwnerOwnings(String ownerId, List<String> cadastres) {
        List<String> previousOwnings = ownerDao.getOwnerOwnings(ownerId);
        List<String> newRelations = cadastres.stream().filter(it -> !previousOwnings.contains(it)).collect(Collectors.toList());
        List<String> removedRelations =
                previousOwnings.stream().filter(it -> !cadastres.contains(it)).collect(Collectors.toList());

        ownerDao.updateOwnerCadastres(ownerId, cadastres);

        if (!removedRelations.isEmpty() || !newRelations.isEmpty()) {
            StringBuilder logMessage = new StringBuilder();
            if (!removedRelations.isEmpty()) {
                logMessage.append("Cadastres have been removed from owner:\n");
                for (String removedRelation : removedRelations) {
                    logMessage.append(removedRelation).append("\n");
                }
                logMessage.append("\n");
            }
            if (!newRelations.isEmpty()) {
                logMessage.append("Cadastres have been added to owner:\n");
                for (String newRelation : newRelations) {
                    logMessage.append(newRelation).append("\n");
                }
            }
            LogMessage message = new LogMessage();
            message.setMessage(logMessage.toString());
            message.setOwner(ownerId);
            message.setCreator("Metsis-System");
            ownerLogService.writeLog(message);
        }

    }

    public void addNewOwner(String ownerId, String ownerName, String ownerType, String loggedInUser) {
        if (ownerDao.findOwner(ownerId).isPresent()) {
            throw new BadRequestException("ADD_OWNER_OWNER_ALREADY_EXISTS");
        }
        ownerDao.addOwner(ownerId, ownerName, ownerType);
        addFollowing(loggedInUser, ownerId);
    }

    public List<ForestNotificationModel> getCadastreNotifications(String cadastre, boolean refreshCashes) {
        return getCadastreNotifications(cadastre, refreshCashes, false);
    }

    public List<ForestNotificationModel> getCadastreNotifications(String cadastre, boolean refreshCashes, boolean includeArchived) {
        List<ForestNotificationModel> notifications = ownerDao.getCadastreNotifications(cadastre, includeArchived);
        if (notifications.isEmpty() || refreshCashes) {
            try {
                List<ForestNotificationModel> freshNotifications = forestRegistryService.getNotificationsForCadastre(cadastre);
                if (!freshNotifications.isEmpty()) {
                    ownerDao.updateNotificationsForCadastre(cadastre, freshNotifications);
                    return ownerDao.getCadastreNotifications(cadastre, includeArchived);
                }
            } catch (Exception e) {
                logger.error("Fetching notifications from metsaregister failed", e);
                return notifications;
            }
        }
        return notifications;
    }

    public List<ForestRegistryFeature> getForestRegistryFeatures(String cadastre) {
        return ownerDao.getForestRegistryFeatures(cadastre);
    }

    public void addFollowing(String user, String owner) {
        if (user == null) {
            return;
        }
        List<String> currentFollowings = getOwnerFollowings(owner);
        if (!currentFollowings.contains(user)) {
            ownerDao.addOwnerFollowing(owner, user);
        }
    }

    public void removeFollowing(String user, String owner) {
        ownerDao.removeOwnerFollowing(owner, user);
    }

    public List<String> getOwnerFollowings(String owner) {
        return ownerDao.getOwnerFollowings(owner);
    }

}
