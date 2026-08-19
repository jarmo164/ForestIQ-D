package ee.metsis.contracts;

import ee.finenet.fineframe.db.AbstractDAO;
import ee.finenet.fineframe.db.DBUtility;
import ee.finenet.fineframe.serialization.GsonHolder;

import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import java.util.stream.Collectors;

import javax.sql.DataSource;

public class ContractDao extends AbstractDAO {
    public ContractDao(DataSource ds) {
        super(ds);
    }

    public byte[] getContractById(String id) {
        return queryForOne("select contract from contracts where id = ?", rs -> getBytes("contract", rs), id);
    }

    public ContractIds saveContract(byte[] contract, String baseId) {
        String id = UUID.randomUUID().toString();
        update("insert into contracts (id, contract, base_id) values(?, ?, ?)", id, contract, baseId);
        return new ContractIds(id, baseId);
    }

    public void deleteExpiredDownloads() {
        Date expiration = new Date(System.currentTimeMillis() - 120000);
        update("delete from contracts where created < ?", DBUtility.fromUtiltoSqlTimestamp(expiration));
    }

    public Optional<ContractData> getHistoricalContractData(String id) {
        return Optional.ofNullable(queryForOne("select data from contract_history where id = ?",
                rs -> GsonHolder.GSON.fromJson(getString("data", rs), ContractData.class), id));
    }

    public String saveContractBase(ContractData contractData) {
        String contractBaseId = UUID.randomUUID().toString();
        update("insert into contract_history (id, sellers, buyer, contract_no, cadastres, created, data) values (?,?,?,?,?,NOW(),?)",
                contractBaseId,
                contractData.getSellers().stream().map(SellerParty::getName).collect(Collectors.joining( ", " )),
                contractData.getBuyer().getName(),
                contractData.getContractNumber(),
                contractData.getContractDetails().getCadastres().stream().map(ContractualCadastre::getId).collect(Collectors.joining( ", " )),
                GsonHolder.GSON.toJson(contractData));
        return contractBaseId;
    }

    public List<HistoricalContractInfo> getHistory(HistoricalContractSearchFilter filter) {
        String sql = "select id, sellers, buyer, contract_no, created from contract_history where 1=1";
        List<Object> params = new ArrayList<>();
        if (filter.getCadastre().isPresent()) {
            params.add(DBUtility.likeParam(filter.getCadastre().get()));
            sql += " and lower(cadastres) like ?";
        }
        if (filter.getBuyer().isPresent()) {
            params.add(DBUtility.likeParam(filter.getBuyer().get().toLowerCase()));
            sql += " and lower(buyer) like ?";
        }
        if (filter.getSeller().isPresent()) {
            params.add(DBUtility.likeParam(filter.getSeller().get().toLowerCase()));
            sql += " and lower(sellers) like ?";
        }
        return queryForList(sql + " order by created desc limit 10 offset " + filter.getOffset(), rs -> {
            HistoricalContractInfo historicalContractInfo = new HistoricalContractInfo();
            historicalContractInfo.setId(getString("id", rs));
            historicalContractInfo.setSellers(getString("sellers", rs));
            historicalContractInfo.setBuyer(getString("buyer", rs));
            historicalContractInfo.setContractNo(getString("contract_no", rs));
            historicalContractInfo.setCreated(getTime("created", rs));
            return historicalContractInfo;
        }, params.toArray());
    }

    public void deleteContract(String id) {
        update("delete from contract_history where id = ?", id);
    }
}
