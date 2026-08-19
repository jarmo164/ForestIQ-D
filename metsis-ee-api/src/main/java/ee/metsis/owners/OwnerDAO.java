package ee.metsis.owners;

import ee.finenet.fineframe.db.AbstractDAO;
import ee.finenet.fineframe.db.DBUtility;
import ee.finenet.fineframe.db.RowHandler;
import ee.finenet.fineframe.exceptions.BadRequestException;
import ee.finenet.fineframe.geography.LatLng;
import ee.finenet.fineframe.user.UserMinimal;
import ee.finenet.fineframe.utilities.CollectionUtility;
import ee.finenet.fineframe.utilities.PolygonUtilty;
import ee.maaamet.geoportaal.xgis.GeoDetails;
import ee.metsad.register.models.ForestNotificationModel;
import ee.metsis.adminworkdesk.AdminWorkdeskSearchRequest;
import ee.metsis.owners.cadastres.Areas;
import ee.metsis.owners.cadastres.Cadastre;
import ee.metsis.owners.cadastres.CadastreMinimal;
import ee.metsis.owners.cadastres.cadastrelabels.CadastreLabel;
import ee.metsis.owners.cadastres.cadastrelabels.ForestPlanCadastreSubPart;
import ee.metsis.owners.cadastres.mk.ForestPlan;
import ee.metsis.owners.cadastres.registryfeatures.ForestRegistryFeature;
import ee.metsis.owners.workdesk.cadastreevaluation.CadastreEvaluation;
import ee.metsis.owners.workdesk.ownerstatus.OwnerDisabledInAdminSearchToken;
import ee.metsis.owners.workdesk.ownerstatus.OwnerStatus;
import ee.metsis.pria.CadastrePolygon;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.sql.ResultSet;
import java.sql.Timestamp;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

import javax.sql.DataSource;

import static ee.finenet.fineframe.db.DBUtility.createQMarks;
import static ee.finenet.fineframe.db.DBUtility.likeParam;
import static ee.finenet.fineframe.serialization.GsonHolder.GSON;

public class OwnerDAO extends AbstractDAO {

    private static final Logger logger = LoggerFactory.getLogger(OwnerDAO.class);

    public OwnerDAO(DataSource ds) {
        super(ds);
    }

    public List<OwnerMinimal> searchOwners(OwnerSearchCriteria criteria) {
        Optional<String> id = criteria.getId();
        Optional<String> name = criteria.getName();
        Optional<String> phone = criteria.getPhone();
        Optional<String> email = criteria.getEmail();
        Optional<String> cadastre = criteria.getCadastre();
        Optional<Long> limit = criteria.getLimit();
        Optional<String> orderBy = criteria.getOrderBy();
        List<String> statuses = criteria.getStatuses();
        Optional<String> assignee = criteria.getAssignee();
        Optional<String> direction = criteria.getDirection();

        StringBuilder sql = new StringBuilder("select distinct " +
                "o.id as owner_id, " +
                "o.name as owner_name, " +
                "o.phone as owner_phone, " +
                "o.status as owner_status, " +
                "u.id as assignee_id, " +
                "u.fullname as assignee_name, " +
                "u.id as assignee_id, " +
                "o.status_set_at as owner_status_set_at " +
                "from owners o " +
                "left join users u on u.id = o.caller_id " +
                "left join owner_cadastre oc on o.id = oc.owner_id " +
                "where 1 = 1");
        List<Object> params = new ArrayList<>();

        if (id.isPresent()) {
            sql.append(" and o.id = ?");
            params.add(id.get());
        }
        if (name.isPresent()) {
            sql.append(" and lower(o.name) like ?");
            params.add(likeParam(name.get().toLowerCase()));
        }
        if (phone.isPresent()) {
            sql.append(" and lower(o.phone) like ?");
            params.add(likeParam(phone.get().toLowerCase()));
        }
        if (email.isPresent()) {
            sql.append(" and lower(o.email) like ?");
            params.add(likeParam(email.get().toLowerCase()));
        }
        if (!statuses.isEmpty()) {
            sql.append(" and status in (").append(DBUtility.createQMarks(statuses.size())).append(")");
            params.addAll(statuses);
        }

        if (cadastre.isPresent()) {
            sql.append(" and oc.cadastre_id = ?");
            params.add(cadastre.get());
        }

        if (assignee.isPresent()) {
            sql.append(" and caller_id = ?");
            params.add(assignee.get());
        }

        sql.append(" order by o.").append(orderBy.orElse("id")).append(" ").append(direction.orElse("asc"));
        sql.append(" limit ").append(limit.orElse(1000L));
        return queryForList(sql.toString(), ownerMinimalHandler(), params.toArray());
    }

    public Optional<Owner> findOwner(String id) {
        List<CadastreMinimal> ownerCadastres = getOwnerCadastresOverview(id);
        return Optional.ofNullable(
                queryForOne("select * from owners where id = ?", rs -> ownerResultSetHandler(ownerCadastres, rs), id)
        );
    }

    public List<String> getOwnerFollowings(String ownerId) {
        return queryForList("select user_id from owner_followings where owner_id = ?",
                rs -> getString("user_id", rs), ownerId);
    }

    public void addOwnerFollowing(String ownerId, String userId) {
        update("insert into owner_followings (user_id, owner_id) values (?, ?)", userId, ownerId);
    }

    public void removeOwnerFollowing(String ownerId, String userId) {
        update("delete from owner_followings where user_id = ? and owner_id = ?", userId, ownerId);
    }

    private Owner ownerResultSetHandler(List<CadastreMinimal> ownerCadastres, ResultSet rs) {
        Owner owner = new Owner();
        owner.setId(getString("id", rs));
        owner.setName(getString("name", rs));
        owner.setType(getString("type", rs));
        owner.setEmail(getString("email", rs));
        owner.setAddress(getString("address", rs));
        owner.setPhone(getString("phone", rs));
        owner.setInfo(getString("info", rs));
        owner.setStatus(getString("status", rs));
        owner.setStatusSetAt(getTime("status_set_at", rs));
        String callerId = getString("caller_id", rs);
        owner.setLastCadastreListRefresh(getLong("last_cadastre_list_refresh", rs));
        owner.setAssignee(getUserMinimal(callerId));
        owner.setCadastres(ownerCadastres);
        return owner;
    }

    private UserMinimal getUserMinimal(String callerId) {
        if (callerId == null) {
            return new UserMinimal();
        }
        return queryForOne("select id, fullname from users where id = ? and ivisible = false",
                rs -> new UserMinimal(getString("id", rs), getString("fullname", rs)), callerId);
    }

    private List<CadastreMinimal> getOwnerCadastresOverview(String ownerId) {
        return queryForList("select c.id, c.name, c.centroid, c.polygon, c.area, c.marked, c.type from cadastres c " +
                "join owner_cadastre oc on oc.cadastre_id = c.id where oc.owner_id = ?", rs -> {
            CadastreMinimal cadastre = new CadastreMinimal();
            cadastre.setId(getString("id", rs));
            cadastre.setName(getString("name", rs));
            String centroid = getString("centroid", rs);
            String polygon = getString("polygon", rs);
            List<List<LatLng>> polygonCoordinates = PolygonUtilty.deserializePolygon(polygon);
            cadastre.setPolygon(polygonCoordinates);
            cadastre.setCentroid(centroid == null ? PolygonUtilty.approximateCentroid(polygonCoordinates) : GSON.fromJson(centroid, LatLng.class));
            cadastre.setArea(getDouble("area", rs));
            cadastre.setMarked(getBoolean("marked", rs));
            cadastre.setType(getString("type", rs));
            return cadastre;
        }, ownerId);
    }

    public void saveOwnerChanges(Owner owner) {
        update("update owners set name = ?, phone = ?, type = ?, email = ?, address = ?, info = ? where id = ?",
                owner.getName(), owner.getPhone(), owner.getType(), owner.getEmail(), owner.getAddress(), owner.getInfo(), owner.getId());
    }

    public Optional<Cadastre> findCadastre(String id) {
        List<OwnerMinimal> owners = findCadastreOwners(id);
        List<CadastreLabel> labels = findCadastreLabels(id);
        return Optional.ofNullable(queryForOne("select * from cadastres where id = ?", rs -> {
            Cadastre cadastre = new Cadastre();
            cadastre.setId(getString("id", rs));
            cadastre.setName(getString("name", rs));
            cadastre.setAddress(getString("address", rs));
            cadastre.setCounty(getString("county", rs));
            cadastre.setMunicipality(getString("municipality", rs));
            cadastre.setPostal(getString("postal", rs));
            cadastre.setRegNr(getString("reg_nr", rs));
            cadastre.setType(getString("type", rs));
            cadastre.setArea(getDouble("area", rs));
            List<List<LatLng>> polygonCoordinates = PolygonUtilty.deserializePolygon(getString("polygon", rs));
            cadastre.setPolygon(polygonCoordinates);
            String centroid = getString("centroid", rs);
            cadastre.setCentroid(centroid == null ? PolygonUtilty.approximateCentroid(polygonCoordinates) : GSON.fromJson(centroid, ee.finenet.fineframe.geography.LatLng.class));
            cadastre.setCadastreSubParts(getCadastreSubparts(id));
            cadastre.setOwners(owners);
            cadastre.setLabels(labels);
            cadastre.setMkDate(getLong("mk_date", rs));
            return cadastre;
        }, id));
    }

    public Optional<Areas> getCadastreAreas(String cadastreId) {
        return Optional.ofNullable(
                queryForOne("select area, yard_area, forest_area, arable_area, meadow_area, meadow_area, underwater_area, buildings_area, other_area from cadastres where id = ?", rs -> {
                    Areas cadastre = new Areas();
                    Double area = getDouble("area", rs);
                    if (area == null) {
                        return null;
                    }
                    cadastre.setArea(area);
                    cadastre.setYardArea(getDouble("yard_area", rs));
                    cadastre.setForestArea(getDouble("forest_area", rs));
                    cadastre.setArableArea(getDouble("arable_area", rs));
                    cadastre.setMeadowArea(getDouble("meadow_area", rs));
                    cadastre.setUnderWaterArea(getDouble("underwater_area", rs));
                    cadastre.setBuildingsArea(getDouble("buildings_area", rs));
                    cadastre.setOtherArea(getDouble("other_area", rs));
                    return cadastre;
                }, cadastreId)
        );
    }

    public void updateCadastreAreas(String cadastreId, Areas areas) {
        update("update cadastres set area = ?, yard_area = ?, forest_area = ?, arable_area = ?," +
                        " meadow_area = ?, underwater_area = ?, buildings_area = ?, other_area = ? where id = ?",
                areas.getArea(),
                areas.getYardArea(),
                areas.getForestArea(),
                areas.getArableArea(),
                areas.getMeadowArea(),
                areas.getUnderWaterArea(),
                areas.getBuildingsArea(),
                areas.getOtherArea(),
                cadastreId);
    }

    private List<ForestPlanCadastreSubPart> getCadastreSubparts(String cadastreNo) {
        return queryForList("select * from cadastre_sub_parts where cadastre_id = ?",
                rs -> {
                    ForestPlanCadastreSubPart cadastreSubPart = new ForestPlanCadastreSubPart();
                    cadastreSubPart.setArea(getDouble("area", rs));
                    cadastreSubPart.setPolygon(PolygonUtilty.deserializePolygon(getString("polygon", rs)));
                    cadastreSubPart.setTreeTypeCode(getString("tree_type_code", rs));
                    cadastreSubPart.setSubPartCode(getInt("sub_part_code", rs));
                    return cadastreSubPart;
                }, cadastreNo);
    }

    private List<CadastreLabel> findCadastreLabels(String cadastreId) {
        return queryForList("select id from cadastre_labels where cadastre_id = ?", rs -> CadastreLabel.fromString(getString("id", rs)), cadastreId);
    }

    public void addLabelToCadastre(String cadastreId, CadastreLabel label) {
        update("insert into cadastre_labels (id, cadastre_id) values (?, ?)", label.name(), cadastreId);
    }

    public void removeLabelFromCadastre(String cadastreId, CadastreLabel label) {
        update("delete from cadastre_labels where id = ? and cadastre_id = ?", label.name(), cadastreId);
    }

    private List<OwnerMinimal> findCadastreOwners(String cadastreId) {
        return queryForList("select distinct o.id as owner_id, o.phone as owner_phone, o.name as owner_name, o.status as owner_status, u.id as assignee_id, u.fullname as assignee_name, o.status_set_at as owner_status_set_at from owners o join owner_cadastre oc on o.id = oc.owner_id left join users u on u.id = o.caller_id where oc.cadastre_id = ?",
                ownerMinimalHandler(), cadastreId);
    }


    public List<String> getDistinctOwnerTypes() {
        return queryForList("select distinct type from owners", rs -> getString("type", rs));
    }

    public List<String> getDistinctMunicipalities() {
        return queryForList("select distinct municipality from cadastres where municipality is not null order by municipality", rs -> getString("municipality", rs));
    }

    public List<String> getDistinctCounties() {
        return queryForList("select distinct county from cadastres where county is not null order by county", rs -> getString("county", rs));
    }


    public List<OwnerMinimal> searchOwnersForAdminWorkdesk(AdminWorkdeskSearchRequest criteria) {
        StringBuilder sql = new StringBuilder("select * from (select distinct o.id as owner_id, o.name as owner_name, o.status as owner_status, o.phone as owner_phone, " +
                "u.id as assignee_id, u.fullname as assignee_name, o.status_set_at as owner_status_set_at from owners o left join users u on u.id = o.caller_id join " +
                "owner_cadastre oc on oc.owner_id = o.id join cadastres c on oc.cadastre_id = c.id left join cadastre_notifications cn on cn.cadastre_id = c.id " +
                "where 1 = 1 ");
        List<Object> params = new ArrayList<>();

        if (criteria.getConservationAreas() == AdminWorkdeskSearchRequest.Conservations.YES) {
            sql.append(" and exists (select id from cadastre_labels where id = ? and cadastre_id = c.id)");
            params.add(CadastreLabel.CONSERVATION_AREA.name());
        } else if (criteria.getConservationAreas() == AdminWorkdeskSearchRequest.Conservations.NO) {
            sql.append(" and not exists (select id from cadastre_labels where id = ? and cadastre_id = c.id)");
            params.add(CadastreLabel.CONSERVATION_AREA.name());
        }

        if (criteria.mustHavePhoneNumber()) {
            sql.append(" and o.phone is not null");
        }

        if (criteria.mustNotHavePhoneNumber()) {
            sql.append(" and o.phone is null");
        }

        if (criteria.mustHaveNoStatus()) {
            sql.append(" and o.status is null");
        }

        Optional<String> status = criteria.getStatus();
        if (status.isPresent()) {
            sql.append(" and o.status = ?");
            params.add(status.get());
        }

        List<String> assignees = criteria.getAssignees();
        if (!assignees.isEmpty()) {
            sql.append(" and o.caller_id in (").append(DBUtility.createQMarks(assignees.size())).append(")");
            params.addAll(assignees);
        }
        if (!criteria.getOwnerTypes().isEmpty()) {
            sql.append(" and o.type in (").append(DBUtility.createQMarks(criteria.getOwnerTypes().size())).append(")");
            params.addAll(criteria.getOwnerTypes());
        }

        if (!criteria.getCounties().isEmpty()) {
            sql.append(" and c.county in (").append(DBUtility.createQMarks(criteria.getCounties().size())).append(")");
            params.addAll(criteria.getCounties());
        }

        if (!criteria.getMunicipalities().isEmpty()) {
            sql.append(" and c.municipality in (").append(DBUtility.createQMarks(criteria.getMunicipalities().size())).append(")");
            params.addAll(criteria.getMunicipalities());
        }

        if (criteria.getArea().getMin().isPresent()) {
            sql.append(" and c.area >= ?");
            params.add(criteria.getArea().getMin().get());
        }
        if (criteria.getArea().getMax().isPresent()) {
            sql.append(" and c.area <= ?");
            params.add(criteria.getArea().getMax().get());
        }

        if (criteria.getArableArea().getMin().isPresent()) {
            sql.append(" and c.arable_area >= ?");
            params.add(criteria.getArableArea().getMin().get());
        }
        if (criteria.getArableArea().getMax().isPresent()) {
            sql.append(" and c.arable_area <= ?");
            params.add(criteria.getArableArea().getMax().get());
        }

        if (criteria.getForrestArea().getMin().isPresent()) {
            sql.append(" and c.forest_area >= ?");
            params.add(criteria.getForrestArea().getMin().get());
        }
        if (criteria.getForrestArea().getMax().isPresent()) {
            sql.append(" and c.forest_area <= ?");
            params.add(criteria.getForrestArea().getMax().get());
        }

        if (criteria.getHasNotificationsSince().isPresent()) {
            sql.append(" and cn.registration_date >= ?");
            params.add(criteria.getHasNotificationsSince().get());
        }

        if (criteria.getHasForrestPlanSince().isPresent()) {
            sql.append(" and c.mk_date >= ?");
            params.add(criteria.getHasForrestPlanSince().get());
        }

        if (criteria.getStatusUpdatedSince().isPresent()) {
            sql.append(" and o.status_set_at >= ?");
            params.add(new Timestamp(criteria.getStatusUpdatedSince().get()));
        }

        if (criteria.getStatusUpdatedTo().isPresent()) {
            sql.append(" and o.status_set_at <= ?");
            params.add(new Timestamp(criteria.getStatusUpdatedTo().get()));
        }

        if (criteria.mustNotHaveForestPlan()) {
            sql.append(" and c.mk_date is null");
        }

        if (status.isEmpty()) {
            List<String> suspensionReason = criteria.getSuspended();
            if (suspensionReason.isEmpty()) {
                sql.append(" and (o.out_of_admin_search_from is null or o.out_of_admin_search_from > NOW() or (o.out_of_admin_search_from <= NOW() and o.out_of_admin_search_to is not null and o.out_of_admin_search_to < NOW()))");
            } else {
                sql.append(" and (o.out_of_admin_search_reason in (")
                        .append(createQMarks(suspensionReason.size()))
                        .append("))");
                params.addAll(suspensionReason);
            }
        }
        sql.append(") xyz order by random()");
        sql.append(" limit ").append(criteria.getMaxResults().orElse(1000L));

        logger.info("Admin worksearch SQL: {}\nParams: {}", sql, params);
        return queryForList(
                sql.toString(),
                rs -> new OwnerMinimal(
                        getString("owner_id", rs),
                        getString("owner_name", rs),
                        getString("owner_status", rs),
                        getTime("owner_status_set_at", rs),
                        new UserMinimal(
                                getString("assignee_id", rs),
                                getString("assignee_name", rs)),
                        getString("owner_phone", rs)), params.toArray());
    }

    private RowHandler<OwnerMinimal> ownerMinimalHandler() {
        return rs -> new OwnerMinimal(
                getString("owner_id", rs),
                getString("owner_name", rs),
                getString("owner_status", rs),
                getTime("owner_status_set_at", rs),
                new UserMinimal(
                        getString("assignee_id", rs),
                        getString("assignee_name", rs)),
                getString("owner_phone", rs)
        );
    }

    public void setCallerForOwners(String assignee, List<String> owners) {
        List<Object> params = new ArrayList<>();
        params.add(assignee);
        params.addAll(owners);
        update("update owners set caller_id = ? where id in (" + DBUtility.createQMarks(owners.size()) + ")", params.toArray());
    }

    public void setStatusForOwners(String status, List<String> owners) {
        List<Object> params = new ArrayList<>();
        OwnerDisabledInAdminSearchToken token = getOwnerStatusById(status)
                .orElseThrow(() -> new BadRequestException("NO_SUCH_OWNER_STATUS")).releaseOwnerOutOfSearchToken();
        params.add(status);
        params.add(DBUtility.fromUtiltoSqlTimestamp(token.getValidFrom()));
        params.add(DBUtility.fromUtiltoSqlTimestamp(token.getValidUntil()));
        params.add(token.getReason());
        params.addAll(owners);
        update("update owners set status = ?, status_set_at = NOW(), out_of_admin_search_from = ?, out_of_admin_search_to = ?, out_of_admin_search_reason = ? where id in (" + DBUtility.createQMarks(owners.size()) + ")", params.toArray());
    }

    public Optional<OwnerStatus> getOwnerStatusById(String id) {
        return Optional.ofNullable(queryForOne("select * from owner_statuses where id = ?", rs -> {
            OwnerStatus os = new OwnerStatus();
            os.setId(getString("id", rs));
            os.setColorHex(getString("reason_color", rs));
            os.setProtectedReason(getBoolean("protected", rs));
            os.setDurationDays(getInt("days_out_of_search", rs));
            return os;
        }, id));
    }

    public Optional<CadastreEvaluation> getCadastreEvaluation(String cadastreNo) {
        return Optional.ofNullable(queryForOne("select our_price, owners_price from cadastres where id = ?", rs -> {
            CadastreEvaluation evaluation = new CadastreEvaluation();
            evaluation.setOurPrice(getString("our_price", rs));
            evaluation.setOwnerPrice(getString("owners_price", rs));
            return evaluation;
        }, cadastreNo));
    }

    public void saveEvaluation(String cadastreId, CadastreEvaluation evaluation) {
        update("update cadastres set our_price = ?, owners_price = ? where id = ?", evaluation.getOurPrice(), evaluation.getOwnerPrice(), cadastreId);
    }

    public void deleteCadastreMarkingsForOwner(String ownerId) {
        update("update cadastres set marked = false where id in (" +
                "select distinct cadastre_id from owner_cadastre where owner_id = ?)", ownerId);
    }

    public void markCadastresForOwner(String ownerId, List<String> markedCadastres) {
        List<Object> params = new ArrayList<>();
        params.add(ownerId);
        params.addAll(markedCadastres);
        update("update cadastres set marked = true where id in (" +
                "select distinct cadastre_id from owner_cadastre where owner_id = ? and cadastre_id in (" +
                DBUtility.createQMarks(markedCadastres.size()) + "))", params.toArray());
    }

    public List<OwnerMinimal> searchOwnersByStatus(String status) {
        return queryForList("select o.id as owner_id, o.name as owner_name, o.phone as owner_phone, o.status as owner_status, u.id as assignee_id, u.fullname as assignee_name, o.status_set_at as owner_status_set_at from owners o left join users u on u.id = o.caller_id where o.status = ? order by o.status_set_at asc",
                ownerMinimalHandler(), status);
    }

    public List<OwnerMinimal> getAllOwnersWithAssignee(String assignee) {
        return queryForList("select o.id as owner_id, o.name as owner_name, o.phone as owner_phone, o.status as owner_status, u.id as assignee_id, u.fullname as assignee_name, o.status_set_at as owner_status_set_at from owners o left join users u on u.id = o.caller_id where o.caller_id = ?",
                ownerMinimalHandler(), assignee);
    }

    public List<OwnerMinimal> getOwnersWithoutStatus(List<String> owners) {
        return queryForList("select o.id as owner_id, o.name as owner_name, o.phone as owner_phone, o.status as owner_status, u.id as assignee_id, u.fullname as assignee_name, o.status_set_at as owner_status_set_at from owners o left join users u on u.id = o.caller_id where o.status is null and o.id in (" + DBUtility.createQMarks(owners.size()) + ")", ownerMinimalHandler(), owners.toArray());
    }

    public Optional<ForestPlan> getMkData(String cadastre) {
        ForestPlan forestPlan = new ForestPlan();
        List<ForestPlanCadastreSubPart> cadastreSubparts = getCadastreSubparts(cadastre);
        if (cadastreSubparts.isEmpty()) {
            return Optional.empty();
        }
        forestPlan.setCadastreNo(cadastre);
        forestPlan.setCadastreSubParts(cadastreSubparts);
        return Optional.of(forestPlan);
    }

    public void insertMkData(ForestPlan forestPlan) {
        update("delete from cadastre_sub_parts where cadastre_id = ?", forestPlan.getCadastreNo());
        CollectionUtility.emptyIfNull(forestPlan.getCadastreSubParts()).forEach(
                part -> update("insert into cadastre_sub_parts (cadastre_id, sub_part_code, tree_type_code, area, polygon) values (?,?,?,?,?)",
                        forestPlan.getCadastreNo(), part.getSubPartCode(), part.getTreeTypeCode(), part.getArea(), PolygonUtilty.serializePolygon(part.getPolygon())));
        update("update cadastres set mk_date = ? where id = ?", forestPlan.getRegistrationDate(), forestPlan.getCadastreNo());
    }

    public List<String> getOwnerOwnings(String ownerId) {
        return queryForList("select cadastre_id from owner_cadastre where owner_id = ?", rs -> getString("cadastre_id", rs), ownerId);
    }

    public void updateOwnerCadastres(String ownerId, List<String> cadastres) {
        update("delete from owner_cadastre where owner_id = ?", ownerId);
        cadastres.forEach(cadastre -> insertCadastreOwnerRelationSilently(ownerId, cadastre));
        update("update owners set last_cadastre_list_refresh = ? where id = ?", System.currentTimeMillis(), ownerId);
    }

    private void insertCadastreOwnerRelationSilently(String owner, String cadastre) {
        try {
            update("insert into owner_cadastre (owner_id, cadastre_id) values (?,?)", owner, cadastre);
        } catch (Exception e) {
            logger.warn("Inserting owner_cadastre relation failed", e);
        }
    }

    public boolean cadastreExists(String cadastre) {
        return queryForOne("select count(*) as cnt from cadastres where id = ?", rs -> getInt("cnt", rs), cadastre) > 0;
    }

    public void insertCadastre(String cadastre, CadastrePolygon cadastrePolygon, GeoDetails detailedInfo) {
        update("insert into cadastres (id, polygon, centroid, municipality, county, type, name) values (?,?,?,?,?,?,?)",
                cadastre,
                PolygonUtilty.serializePolygon(cadastrePolygon.getCoordinates()),
                PolygonUtilty.serializeCentroid(cadastrePolygon.getCentroid()),
                detailedInfo.getVald(),
                detailedInfo.getMaakond(),
                detailedInfo.getType(),
                detailedInfo.getKinnistuNimi());
    }

    public void updateGeoDetails(String cadastre, GeoDetails geoDetails) {
        update("update cadastres set municipality = ?, county = ?, type = ?, name = ? where id = ?",
                geoDetails.getVald(),
                geoDetails.getMaakond(),
                geoDetails.getType(),
                geoDetails.getKinnistuNimi(),
                cadastre);
    }

    public void addOwner(String ownerId, String ownerName, String ownerType) {
        update("insert into owners (id, name, type) values (?, ?, ?)", ownerId,
                ownerName.length() > 100 ? ownerName.substring(100) : ownerName,
                ownerType
        );
    }

    public List<ForestNotificationModel> getCadastreNotifications(String cadastre, boolean includeArchived) {
        String archiveFilter = includeArchived ? "" : " and archived = false";
        return queryForList("select * from cadastre_notifications where cadastre_id = ?" + archiveFilter + " order by archived asc, registration_date asc, cadastre_subpart_code asc",
                cadastreNotificationMapper(), cadastre);
    }

    public void updateNotificationsForCadastre(String cadastre, List<ForestNotificationModel> notifications) {
        update("delete from cadastre_notifications where cadastre_id = ? and archived = false", cadastre);
        notifications.forEach(notification -> this.insertNotificationForCadastre(cadastre, notification));
    }

    private RowHandler<ForestNotificationModel> cadastreNotificationMapper() {
        return rs -> {
            ForestNotificationModel notification = new ForestNotificationModel();
            notification.setNotificationId(getLong("id", rs));
            notification.setNotificationNumber(getLong("notification_number", rs));
            notification.setAmountToBeCut(getDouble("amount_to_be_cut", rs));
            notification.setArea(getDouble("area", rs));
            notification.setCadastreSubPartCode(getLong("cadastre_subpart_code", rs));
            notification.setDamageCode(getString("damage_code", rs));
            notification.setConfirmationDate(getLong("confirmation_date", rs));
            notification.setRegistrationDate(getLong("registration_date", rs));
            String decision = getString("decision", rs);
            notification.setDecision(decision);
            notification.setState(getLong("state", rs));
            notification.setWorkCode(getString("work_code", rs));
            notification.setCadastreNo(getString("cadastre_id", rs));
            notification.setArchived(getBoolean("archived", rs));
            notification.setArchiveDate(getLong("archive_date", rs));
            return notification;
        };
    }

    public void insertNotificationForCadastre(String cadastre, ForestNotificationModel notification) {
        update("insert into cadastre_notifications (" +
                        "cadastre_id, " +
                        "id, " +
                        "notification_number, " +
                        "amount_to_be_cut, " +
                        "area, " +
                        "cadastre_subpart_code, " +
                        "damage_code, " +
                        "confirmation_date, " +
                        "registration_date, " +
                        "decision, " +
                        "state, " +
                        "work_code" +
                        ") values (?,?,?,?,?,?,?,?,?,?,?,?)",
                cadastre,
                notification.getNotificationId(),
                notification.getNotificationNumber(),
                notification.getAmountToBeCut(),
                notification.getArea(),
                notification.getCadastreSubPartCode(),
                notification.getDamageCode(),
                notification.getConfirmationDate(),
                notification.getRegistrationDate(),
                notification.getDecision(),
                notification.getState(),
                notification.getWorkCode());
    }

    public List<ForestRegistryFeature> getForestRegistryFeatures(String cadastre) {
        return queryForList("select * from forest_registry_features where cadastre_id = ? order by source_layer asc, event_date desc nulls last, subpart_code asc nulls last",
                rs -> {
                    ForestRegistryFeature feature = new ForestRegistryFeature();
                    feature.setId(getLong("id", rs));
                    feature.setSourceLayer(getString("source_layer", rs));
                    feature.setSourceId(getString("source_id", rs));
                    feature.setCadastreId(getString("cadastre_id", rs));
                    feature.setSubpartCode(getInt("subpart_code", rs));
                    feature.setTitle(getString("title", rs));
                    feature.setWorkCode(getString("work_code", rs));
                    feature.setDecision(getString("decision", rs));
                    feature.setArea(getDouble("area", rs));
                    feature.setVolume(getDouble("volume", rs));
                    feature.setEventDate(getLong("event_date", rs));
                    feature.setAttributes(getString("attributes", rs));
                    feature.setGeometry(getString("geometry", rs));
                    return feature;
                }, cadastre);
    }

    public List<R> relations(int page) {
        return queryForList("select " +
                        "owners.id as owner_id, " +
                        "owners.name as owner_name, " +
                        "owner_cadastre.cadastre_id as cadastre_id from owner_cadastre " +
                        "join owners on owners.id = owner_cadastre.owner_id order by 1 asc limit 1000 offset ?",
                rs -> new R(
                        getString("owner_id", rs),
                        getString("owner_name", rs),
                        getString("cadastre_id", rs)
                ),
                page * 1000
        );
    }
}
