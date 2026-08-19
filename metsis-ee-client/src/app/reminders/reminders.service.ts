import { Injectable } from '@angular/core';
import {Observable} from 'rxjs';
import {Reminder} from './reminder';
import {ApiErrorHandler} from '../api-error-handler';
import {HttpClient} from '@angular/common/http';
import {catchError} from 'rxjs/operators';
import {NewReminder} from './new-reminder';

@Injectable()
export class RemindersService {

  constructor(private http: HttpClient, private errors: ApiErrorHandler) { }

  getReminders(): Observable<Reminder[]> {
    return this.http.get<Reminder[]>('api/services/reminders').pipe(catchError(this.errors.handle));
  }

  submitNewReminder(reminder: NewReminder): Observable<any> {
    return this.http.post<any>('api/services/reminders', reminder).pipe(catchError(this.errors.handle));
  }

  deleteReminder(id: number): Observable<any> {
    return this.http.delete('api/services/reminders/' + encodeURIComponent(id.toString())).pipe(catchError(this.errors.handle));
  }

  getRemindersDashboard(): Observable<Reminder[]> {
    return this.http.get('api/services/reminders-dashboard').pipe(catchError(this.errors.handle));
  }
}
