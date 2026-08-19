import {Injectable} from '@angular/core';
import {HttpClient} from '@angular/common/http';
import {ApiErrorHandler} from '../api-error-handler';
import {catchError} from 'rxjs/operators';
import {Observable} from 'rxjs';
import {PersonsDumpEntry} from './persons-dump-entry';
import {PersonsDumpCriteria} from './persons-dump-criteria';
import {NewPhonebookEntry} from './new-phonebook-entry';

@Injectable()
export class PersonsDumpService {

  constructor(private http: HttpClient, private errors: ApiErrorHandler) {
  }

  search(criteria: PersonsDumpCriteria): Observable<PersonsDumpEntry[]> {
    let url = 'api/services/persons-dump?1=1';

    if (criteria.source) {
      url += '&source=' + criteria.source;
    }

    if (criteria.code) {
      url += '&code=' + criteria.code;
    }

    if (criteria.name) {
      url += '&name=' + criteria.name;
    }

    if (criteria.phone) {
      url += '&phone=' + criteria.phone;
    }

    if (criteria.address) {
      url += '&address=' + criteria.address;
    }

    return this.http.get<PersonsDumpEntry[]>(url).pipe(catchError(this.errors.handle));
  }

  addEntry(entry: NewPhonebookEntry): Observable<any> {
    return this.http.post('api/services/persons-dump', entry).pipe(catchError(this.errors.handle));
  }

  deleteEntry(id: number) {
    return this.http.delete('api/services/persons-dump/' + id, {}).pipe(catchError(this.errors.handle));
  }
}
