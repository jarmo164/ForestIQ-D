import {Injectable} from '@angular/core';
import {HttpClient} from '@angular/common/http';
import {MaintainableUser} from './maintain-users/maintainable-user';
import {Observable} from 'rxjs';
import {catchError, map} from 'rxjs/operators';
import {ApiErrorHandler} from '../api-error-handler';
import {AddUserResponse} from './add-user-response';
import {OwnerStatus} from "../owners/owner-status-bubble/owner-status";

@Injectable()
export class AdminService {

  constructor(private http: HttpClient, private errors: ApiErrorHandler) {
  }

  getAllMaintainableUsers(): Observable<MaintainableUser[]> {
    return this.http.get<MaintainableUser[]>('api/services/admin/users').pipe(map(data => {
      let result : MaintainableUser[] = [];
      data.forEach((item) => {
        result.push(MaintainableUser.createInstance(item))
      });
      return result
    })).pipe(catchError(this.errors.handle));
  }

  addUser(user: MaintainableUser) {
    return this.http.post<AddUserResponse>('api/services/admin/users', user).pipe(catchError(this.errors.handle));
  }

  deleteUser(user: MaintainableUser): Observable<any> {
    return this.http.delete('api/services/admin/users/' + encodeURIComponent(user.id)).pipe(catchError(this.errors.handle));
  }

  setUserPrivileges(user: MaintainableUser): Observable<any> {
    return this.http.post('api/services/admin/users/' + encodeURIComponent(user.id), user.privileges).pipe(catchError(this.errors.handle));
  }

  getAllOwnerStatuses(): Observable<OwnerStatus[]> {
    return this.http.get<OwnerStatus[]>('api/services/owner-statuses').pipe(catchError(this.errors.handle));
  }

  saveOwnerStatus(status: OwnerStatus): Observable<any> {
    return this.http.post('api/services/owner-statuses', status).pipe(catchError(this.errors.handle));
  }

  deleteOwnerStatus(id: string) {
    return this.http.delete('api/services/owner-statuses/' + encodeURIComponent(id)).pipe(catchError(this.errors.handle));
  }
}
