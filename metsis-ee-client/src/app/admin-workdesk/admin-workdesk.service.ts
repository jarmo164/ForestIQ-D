import {Injectable} from '@angular/core';
import {HttpClient} from '@angular/common/http';
import {ApiErrorHandler} from '../api-error-handler';
import {AdminWorkdeskPreparationData, IAdminWorkdeskPreparationData} from './admin-workdesk-preparation-data';
import {Observable} from 'rxjs';
import {catchError, map} from 'rxjs/operators';
import {Worksearchcriteria} from './worksearchcriteria';
import {OwnerMinimal} from '../owners/owner-minimal';
import {AssignWorkModel} from './assign-work-model';

@Injectable()
export class AdminWorkdeskService {

  constructor(private http: HttpClient, private errors: ApiErrorHandler) {
  }

  getPreparationData(): Observable<AdminWorkdeskPreparationData> {
    return this.http.get<IAdminWorkdeskPreparationData>('api/services/admin-workdesk/prepare').pipe(map(data => {
      return new AdminWorkdeskPreparationData(data);
    })).pipe(catchError(this.errors.handle));
  }

  searchForWork(criteria: Worksearchcriteria): Observable<OwnerMinimal[]> {
    let url = 'api/services/admin-workdesk/owners-search?1=1';

    if (criteria.maxResults) {
      url += '&maxResults=' + criteria.maxResults;
    }

    if (criteria.onlyWithPhoneNumbers) {
      url += '&mustHavePhoneNumber=' + criteria.onlyWithPhoneNumbers;
    }
    if (criteria.onlyWithoutPhoneNumbers) {
      url += '&mustNotHavePhoneNumber=' + criteria.onlyWithoutPhoneNumbers;
    }
    if (criteria.onlyWithoutForestPlans) {
      url += '&mustNotHaveForestPlan=' + criteria.onlyWithoutForestPlans;
    }

    if (criteria.onlyWithNoStatus) {
      url += '&mustHaveNoStatus=' + criteria.onlyWithNoStatus;
    }

    if (criteria.minArea) {
      url += '&minArea=' + criteria.minArea;
    }
    if (criteria.minArableArea) {
      url += '&minArableArea=' + criteria.minArableArea;
    }
    if (criteria.minForrestArea) {
      url += '&minForrestArea=' + criteria.minForrestArea;
    }

    if (criteria.maxArea) {
      url += '&maxArea=' + criteria.maxArea;
    }
    if (criteria.maxArableArea) {
      url += '&maxArableArea=' + criteria.maxArableArea;
    }
    if (criteria.maxForrestArea) {
      url += '&maxForrestArea=' + criteria.maxForrestArea;
    }
    if (criteria.conservationAreas) {
      url += '&conservationAreas=' + encodeURIComponent(criteria.conservationAreas);
    }
    if (criteria.suspendedFor && criteria.suspendedFor.length > 0) {
      url += '&suspended=' + encodeURIComponent(this.arrayToCommaSepparatedString(criteria.suspendedFor));
    }

    if (criteria.counties && criteria.counties.length > 0) {
      url += '&counties=' + encodeURIComponent(this.arrayToCommaSepparatedString(criteria.counties));
    }
    if (criteria.municipalities && criteria.municipalities.length > 0) {
      url += '&municipalities=' + encodeURIComponent(this.arrayToCommaSepparatedString(criteria.municipalities));
    }
    if (criteria.ownerTypes && criteria.ownerTypes.length > 0) {
      url += '&ownerTypes=' + encodeURIComponent(this.arrayToCommaSepparatedString(criteria.ownerTypes));
    }
    if (criteria.status) {
      url += '&status=' + encodeURIComponent(criteria.status);
    }
    if (criteria.assignees && criteria.assignees.length > 0) {
      url += '&assignees=' + encodeURIComponent(this.arrayToCommaSepparatedString(criteria.assignees));
    }
    if (criteria.hasNotificationsSince) {
      url += '&hasNotificationsSince=' + criteria.hasNotificationsSince.getTime();
    }
    if (criteria.hasForrestPlanSince) {
      url += '&hasForrestPlanSince=' + criteria.hasForrestPlanSince.getTime();
    }
    if (criteria.statusUpdatedSince) {
      url += '&statusUpdatedSince=' + criteria.statusUpdatedSince.getTime();
    }
    if (criteria.statusUpdatedTo) {
      url += '&statusUpdatedTo=' + criteria.statusUpdatedTo.getTime();
    }
    return this.http.get<OwnerMinimal[]>(url).pipe(catchError(this.errors.handle));
  }

  assignWork(assignWorkModel: AssignWorkModel): Observable<any> {
    return this.http.post<any>('api/services/admin-workdesk/assign', assignWorkModel).pipe(catchError(this.errors.handle));
  }

  private arrayToCommaSepparatedString(arr: any[]): string {
    let result = '';
    for (let i = 0; i < arr.length; i++) {
      result += arr[i].id;
      if (i !== arr.length - 1) {
        result += ',';
      }
    }
    return result;
  }

}
