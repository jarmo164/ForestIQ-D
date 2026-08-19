import { Injectable } from '@angular/core';
import {BehaviorSubject, Observable, Subject} from 'rxjs';
import {HttpClient} from '@angular/common/http';
import {ApiErrorHandler} from '../api-error-handler';
import {catchError} from 'rxjs/operators';
import {AuthService} from '../auth/auth-service';
import {Message} from './message';
import {Ng2IzitoastService} from 'ng2-izitoast';
import {NewDirectMessage} from './new-direct-message';

const PAUSE_BETWEEN_MESSAGE_COUNT_POLLS = 3000;

@Injectable({
  providedIn: 'root'
})
export class MessagesService {

  constructor(private http: HttpClient, private errors: ApiErrorHandler, private authService: AuthService, private iziToast: Ng2IzitoastService) {
    this.newMessagesCount.next(null);
    this.pollAndPollAndPollNewMessages();
  }

  public newMessagesCount: BehaviorSubject<number> = new BehaviorSubject<number>(null);

  private pollAndPollAndPollNewMessages() {
    if (this.authService.isLoggedIn()) {
      this.getNewMessagesCount().subscribe(
        data => {
          if ((this.newMessagesCount.getValue() >= 0)
            && this.newMessagesCount.getValue() < data.newMessageCount) {
            this.iziToast.success({
              message: 'You\'ve got new messages'
            });
          }
          this.newMessagesCount.next(data.newMessageCount);
          setTimeout(() => this.pollAndPollAndPollNewMessages(), PAUSE_BETWEEN_MESSAGE_COUNT_POLLS);
        }, error => {
          console.error('Polling new message count failed', error);
          this.newMessagesCount.next(null);
          setTimeout(() => this.pollAndPollAndPollNewMessages(), PAUSE_BETWEEN_MESSAGE_COUNT_POLLS);
        }
      );
    } else {
      setTimeout(() => this.pollAndPollAndPollNewMessages(), PAUSE_BETWEEN_MESSAGE_COUNT_POLLS);
    }
  }

  public getReceivedMessages(page: number, size: number): Observable<Message[]> {
    return this.http.get<Message[]>('api/services/messages/received', {
      params: {
        page: `${page}`,
        size: `${size}`
      }
    }).pipe(catchError(this.errors.handle));
  }

  public getSentMessages(page: number, size: number): Observable<Message[]> {
    return this.http.get<Message[]>('api/services/messages/sent', {
      params: {
        page: `${page}`,
        size: `${size}`
      }
    }).pipe(catchError(this.errors.handle));
  }

  private getNewMessagesCount(): Observable<{newMessageCount: number}> {
    return this.http.get<{newMessageCount: number}>('api/services/messages/new/count').pipe(catchError(this.errors.handle));
  }

  markAllReceicedAsRead(newestMessageDate: Date): Observable<any> {
    return this.http.post<any>('api/services/messages/received/mark-as-read', {
      markReadUntil: newestMessageDate
    }).pipe(catchError(this.errors.handle));
  }

  getUserNames(): Observable<string[]> {
    return this.http.get<string[]>('api/services/messages/usernames').pipe(catchError(this.errors.handle));
  }

  sendDirectMessage(message: NewDirectMessage): Observable<any> {
    return this.http.post<any>('api/services/messages/send', message).pipe(catchError(this.errors.handle));
  }
}
