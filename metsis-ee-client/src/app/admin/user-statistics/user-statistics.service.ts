import {Injectable} from '@angular/core';
import {ApiErrorHandler} from '../../api-error-handler';
import {HttpClient} from '@angular/common/http';
import {Observable} from 'rxjs';
import {UserOwnerStatusChangeStatistics} from './user-owner-status-change-statistics';
import {catchError, map} from 'rxjs/operators';
import {GetUserOwnerStatusChangeStatisticsModel} from './get-user-owner-status-change-statistics-model';
import {RequestUtility} from '../../utilities/request-utility';
import {IUserStatisticsPrepData, UserStatisticsPrepData} from './user-statistics-prep-data';

@Injectable()
export class UserStatisticsService {

  constructor(private http: HttpClient, private errors: ApiErrorHandler) {
  }

  getStatistics(criteria: GetUserOwnerStatusChangeStatisticsModel): Observable<UserOwnerStatusChangeStatistics[]> {
    let url = 'api/services/admin/userstatistics/owner-status-change?1=1';
    let users = criteria.getUsers();
    if (users && users.length > 0) {
      url += '&users=' + encodeURIComponent(RequestUtility.arrayToCommaSepparatedString(users));
    }
    let fromStatuses = criteria.getFromStatuses();
    if (fromStatuses && fromStatuses.length > 0) {
      url += '&fromStatuses=' + encodeURIComponent(RequestUtility.arrayToCommaSepparatedString(fromStatuses));
    }
    let toStatuses = criteria.getToStatuses();
    if (toStatuses && toStatuses.length > 0) {
      url += '&toStatuses=' + encodeURIComponent(RequestUtility.arrayToCommaSepparatedString(toStatuses));
    }
    if (criteria.granularity) {
      url += '&granularity=' + encodeURIComponent(criteria.granularity);
    }
    if (criteria.getSince()) {
      url += '&since=' + encodeURIComponent(criteria.getSince().getTime().toString());
    }
    if (criteria.getUpTo()) {
      url += '&upTo=' + encodeURIComponent(criteria.getUpTo().getTime().toString());
    }
    return this.http.get<UserOwnerStatusChangeStatistics[]>(url).pipe(catchError(this.errors.handle));
  }

  getPrepData(): Observable<UserStatisticsPrepData> {
    return this.http.get<IUserStatisticsPrepData>('api/services/admin/userstatistics/prep-data').pipe(map(data => {
      return new UserStatisticsPrepData(data);
    })).pipe(catchError(this.errors.handle));
  }
}
