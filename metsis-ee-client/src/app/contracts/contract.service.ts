import { Injectable } from '@angular/core';
import {ApiErrorHandler} from '../api-error-handler';
import {HttpClient} from '@angular/common/http';
import {catchError} from 'rxjs/operators';
import {Observable} from 'rxjs';
import {ContractData} from './models/contract-data';
import {CreatedContractInfo} from './models/created-contract-info';
import {ContractualCadastre} from './models/contractual-cadastre';
import {ContractParty} from './models/contract-party';
import {HistoricalContractInfo} from './models/historical-contract-info';
import {HistoricalContractsSearchFilter} from './models/historical-contracts-search-filter';

@Injectable()
export class ContractService {

  constructor(private http: HttpClient, private errors: ApiErrorHandler) { }

  getPreparationData(baseContractId?: string): Observable<ContractData> {
    const urlEnd = baseContractId == null ? '' : '?basecontract=' + encodeURIComponent(baseContractId);
    return this.http.get<ContractData>('api/services/contract' + urlEnd).pipe(catchError(this.errors.handle));
  }

  createContract(contract: ContractData): Observable<CreatedContractInfo> {
    return this.http.post<CreatedContractInfo>('api/services/contract', contract).pipe(catchError(this.errors.handle));
  }

  getCadastreDetails(cadastre: string): Observable<ContractualCadastre> {
    return this.http.get<ContractualCadastre>('api/services/autocompleters/cadastre-details/' + encodeURIComponent(cadastre)).pipe(catchError(this.errors.handle));
  }

  getOwnerDetails(id: string): Observable<ContractParty> {
    return this.http.get<ContractParty>('api/services/autocompleters/owner-details/' + encodeURIComponent(id)).pipe(catchError(this.errors.handle));
  }

  listHistoricalContracts(historicalContractsSearchFilter: HistoricalContractsSearchFilter): Observable<HistoricalContractInfo[]> {
    let url = 'api/services/contracts/history?offset=' + historicalContractsSearchFilter.offset;
    if (historicalContractsSearchFilter.cadastre) {
      url += '&cadastre=' + encodeURIComponent(historicalContractsSearchFilter.cadastre);
    }
    if (historicalContractsSearchFilter.buyer) {
      url += '&buyer=' + encodeURIComponent(historicalContractsSearchFilter.buyer);
    }
    if (historicalContractsSearchFilter.seller) {
      url += '&seller=' + encodeURIComponent(historicalContractsSearchFilter.seller);
    }
    return this.http.get<HistoricalContractInfo[]>(url).pipe(catchError(this.errors.handle));

  }

  deleteContract(contractId: string): Observable<any> {
    return this.http.delete('api/services/contract/' + encodeURIComponent(contractId)).pipe(catchError(this.errors.handle));
  }
}
