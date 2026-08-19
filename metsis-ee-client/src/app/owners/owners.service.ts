import {Injectable} from '@angular/core';
import {HttpClient} from '@angular/common/http';
import {ApiErrorHandler} from '../api-error-handler';
import {OwnerSearchCriteria} from './owner-search-criteria';
import {Observable} from 'rxjs';
import {OwnerMinimal} from './owner-minimal';
import {catchError} from 'rxjs/operators';
import {Owner} from './owner-profile/owner';
import {Cadastre} from './owner-profile/cadastre';
import {ChangeOwnerStatusModel} from '../admin-workdesk/change-owner-status-model';
import {OwnerLogMessage} from './owner-profile/owner-log/owner-log-message';
import {CadastreEvaluation} from './owner-profile/cadastre-profile/cadastre-evalutation/cadastre-evaluation';
import {MyWorkSearchCriteria} from '../caller-wordesk/my-work-search-criteria';
import {OwnerStatusData} from './owner-profile/owner-status/owner-status-data';
import {RequestUtility} from '../utilities/request-utility';
import {CadastreLabelsModel} from './owner-profile/cadastre-profile/cadastre-labels/cadastre-labels-model';
import {OwnerId} from './owner-profile/owner-id';
import {MkData} from './owner-profile/cadastre-profile/mk-data';
import {Areas} from './owner-profile/cadastre-profile/areas/areas';
import {CadastreNotification} from './owner-profile/cadastre-profile/cadastre-notifications/cadastre-notification';
import {CallerWorkdeskPrepData} from '../caller-wordesk/caller-workdesk-prep-data';
import {ForestRegistryFeature} from './owner-profile/cadastre-profile/registry-features/forest-registry-feature';

@Injectable()
export class OwnersService {

  constructor(private http: HttpClient, private errors: ApiErrorHandler) {
  }

  searchOwners(criteria: OwnerSearchCriteria): Observable<OwnerMinimal[]> {
    let url = 'api/services/owners?1=1';
    if (criteria.id) {
      url += '&id=' + encodeURIComponent(criteria.id);
    }
    if (criteria.name) {
      url += '&name=' + encodeURIComponent(criteria.name);
    }
    if (criteria.phone) {
      url += '&phone=' + encodeURIComponent(criteria.phone);
    }
    if (criteria.email) {
      url += '&email=' + encodeURIComponent(criteria.email);
    }
    if (criteria.cadastreNo) {
      url += '&cadastre=' + encodeURIComponent(criteria.cadastreNo);
    }
    return this.http.get<OwnerMinimal[]>(url).pipe(catchError(this.errors.handle));
  }

  getOwner(id: string): Observable<Owner> {
    return this.http.get<Owner>('api/services/owners/' + encodeURIComponent(id)).pipe(catchError(this.errors.handle));
  }

  saveOwnerChanges(owner: Owner): Observable<any> {
    return this.http.post<String>('api/services/owners/' + encodeURIComponent(owner.id), owner).pipe(catchError(this.errors.handle));
  }

  getCadastreDetails(id: string): Observable<Cadastre> {
    return this.http.get<Cadastre>('api/services/cadastres/' + encodeURIComponent(id)).pipe(catchError(this.errors.handle));
  }

  changeOwnerStatus(ownerId: string, changeModel: ChangeOwnerStatusModel): Observable<any> {
    return this.http.post<String>('api/services/owners/' + encodeURIComponent(ownerId) + '/change-status', changeModel).pipe(catchError(this.errors.handle));
  }

  getOwnerLog(ownerId: string): Observable<OwnerLogMessage[]> {
    return this.http.get<OwnerLogMessage[]>('api/services/owners/' + encodeURIComponent(ownerId) + '/log').pipe(catchError(this.errors.handle));
  }

  addOwnerLogEntry(ownerId: string, message: string): Observable<OwnerLogMessage[]> {
    return this.http.post<OwnerLogMessage[]>('api/services/owners/' + encodeURIComponent(ownerId) + '/log', {message: message}).pipe(catchError(this.errors.handle));
  }

  getLatestCadastreEvaluation(cadastre: string): Observable<CadastreEvaluation> {
    return this.http.get<CadastreEvaluation>('api/services/cadastres/' + encodeURIComponent(cadastre) + '/evaluation').pipe(catchError(this.errors.handle));
  }

  saveEvaluation(cadastre: string, data: CadastreEvaluation): Observable<any> {
    return this.http.post<String>('api/services/cadastres/' + encodeURIComponent(cadastre) + '/evaluation', data).pipe(catchError(this.errors.handle));
  }

  markInterestingCadastres(ownerId: string, markedCadastres: string[]): Observable<any> {
    return this.http.post<String>('api/services/owners/' + encodeURIComponent(ownerId) + '/mark-cadastres', markedCadastres).pipe(catchError(this.errors.handle));
  }

  getOwnersInNeedOfEvaluation(): Observable<OwnerMinimal[]> {
    return this.http.get<OwnerMinimal[]>('api/services/owners-in-need-of-evaluation').pipe(catchError(this.errors.handle));
  }

  searchMyWork(criteria: MyWorkSearchCriteria): Observable<OwnerMinimal[]> {
    let url = 'api/services/my-work?1=1';
    if (criteria.id) {
      url += '&id=' + encodeURIComponent(criteria.id);
    }
    if (criteria.name) {
      url += '&name=' + encodeURIComponent(criteria.name);
    }
    if (criteria.phone) {
      url += '&phone=' + encodeURIComponent(criteria.phone);
    }
    if (criteria.email) {
      url += '&email=' + encodeURIComponent(criteria.email);
    }
    if (criteria.order) {
      url += '&orderBy=' + encodeURIComponent(criteria.order);
    }
    if (criteria.direction) {
      url += '&direction=' + encodeURIComponent(criteria.direction);
    }
    const statusIds = criteria.statusIds();
    if (statusIds.length) {
      url += '&statuses=' + RequestUtility.arrayToCommaSepparatedString(statusIds.map(id => encodeURIComponent(id)));
    }
    if (criteria.cadastre) {
      url += '&cadastre=' + encodeURIComponent(criteria.cadastre);
    }
    return this.http.get<OwnerMinimal[]>(url).pipe(catchError(this.errors.handle));
  }

  getStatusData(ownerId: string): Observable<OwnerStatusData> {
    return this.http.get<OwnerStatusData>('api/services/owner/' + encodeURIComponent(ownerId) + '/status').pipe(catchError(this.errors.handle));
  }

  changeOwnerAssignee(ownerId: string, newAssignee: string): Observable<string> {
    return this.http.post<String>('api/services/owner/' + encodeURIComponent(ownerId) + '/assignee', {assignee: newAssignee}).pipe(catchError(this.errors.handle));
  }

  getCadastreLabels(cadastreId: string): Observable<CadastreLabelsModel> {
    return this.http.get<CadastreLabelsModel>('api/services/cadastres/' + encodeURIComponent(cadastreId) + '/labels').pipe(catchError(this.errors.handle));
  }

  addCadastreLabel(cadastreId: string, label: string): Observable<any> {
    return this.http.post<CadastreLabelsModel>('api/services/cadastres/' + encodeURIComponent(cadastreId) + '/labels/' + encodeURIComponent(label), {}).pipe(catchError(this.errors.handle));
  }

  removeCadastreLabel(cadastreId: string, label: string): Observable<any> {
    return this.http.delete<CadastreLabelsModel>('api/services/cadastres/' + encodeURIComponent(cadastreId) + '/labels/' + encodeURIComponent(label), {}).pipe(catchError(this.errors.handle));
  }

  getNextOwnerAssignedToMe(): Observable<OwnerId> {
    return this.http.get<CadastreLabelsModel>('api/services/my-work/next-owner').pipe(catchError(this.errors.handle));
  }

  getMkData(cadastreId: string, refreshCaches: boolean): Observable<MkData> {
    return this.http.get<CadastreLabelsModel>('api/services/cadastres/' + encodeURIComponent(cadastreId) + '/mkdata?refreshCaches=' + refreshCaches).pipe(catchError(this.errors.handle));
  }

  getCadastreAreas(cadastreId: string, refreshCaches: boolean): Observable<Areas> {
    return this.http.get<CadastreLabelsModel>('api/services/cadastres/' + encodeURIComponent(cadastreId) + '/areas?refreshCaches=' + refreshCaches).pipe(catchError(this.errors.handle));
  }

  addOwner(ownerId: string, ownerName: string, ownerType: string): Observable<any> {
    return this.http.post<String>('api/services/owners/' + encodeURIComponent(ownerId) + '/add', {
      ownerName: ownerName,
      ownerType: ownerType
    }).pipe(catchError(this.errors.handle));
  }

  getCadastreNotifications(cadastre: string, refreshCaches: boolean, includeArchived: boolean): Observable<CadastreNotification[]> {
    return this.http.get<CadastreNotification[]>('api/services/cadastres/' + encodeURIComponent(cadastre) + '/notifications?refreshCaches=' + refreshCaches + '&includeArchived=' + includeArchived).pipe(catchError(this.errors.handle));
  }

  getForestRegistryFeatures(cadastre: string): Observable<ForestRegistryFeature[]> {
    return this.http.get<ForestRegistryFeature[]>('api/services/cadastres/' + encodeURIComponent(cadastre) + '/registry-features').pipe(catchError(this.errors.handle));
  }

  prepareCallerWorkdesk(): Observable<CallerWorkdeskPrepData> {
    return this.http.get<CadastreLabelsModel>('api/services/caller-workdesk-prep-data').pipe(catchError(this.errors.handle));
  }

  getOwnerFollowers(ownerId: string): Observable<{ followers: string[], potentialFollowers: string[] }> {
    return this.http.get(`api/services/owner/${ownerId}/followings`).pipe(catchError(this.errors.handle));
  }

  disableOwnerNotifications(ownerId: string, userId: string): Observable<any> {
    return this.http.delete(`api/services/owner/${ownerId}/followings/${userId}`).pipe(catchError(this.errors.handle));
  }

  enableOwnerNotifications(ownerId: string, userId: string): Observable<any> {
    return this.http.post(`api/services/owner/${ownerId}/followings/${userId}`, {}).pipe(catchError(this.errors.handle));
  }
}
