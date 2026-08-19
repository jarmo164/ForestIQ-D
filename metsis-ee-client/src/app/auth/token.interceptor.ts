
import {throwError as observableThrowError, empty as observableEmpty, Observable, Subject, Subscription} from 'rxjs';

import {switchMap, catchError} from 'rxjs/operators';
import {AuthService} from './auth-service';
import {Injectable} from '@angular/core';
import {HttpHandler, HttpInterceptor, HttpRequest} from '@angular/common/http';
import {ApiErrorCode} from '../api.error.code';

@Injectable()
export class TokenInterceptor implements HttpInterceptor {

  refreshTokenInProgress = false;
  tokenRefreshedSource = new Subject();
  tokenRefreshed$ = this.tokenRefreshedSource.asObservable();

  constructor(public auth: AuthService) {
  }

  intercept(request: HttpRequest<any>, next: HttpHandler): Observable<any> {
    const url = request.url;
    const securedRequest = url.startsWith('api/services') && !url.startsWith('api/services/token-refresh');
    if (securedRequest) {
      const token = this.auth.getToken();
      if (token != null) {
        request = this.applyCredentials(request, token);
        return next.handle(request).pipe(catchError((err) => {
          if (this.isInvalidTokenError(err)) {
            return this.refreshToken().pipe(
              switchMap(() => {
                request = this.applyCredentials(request, this.auth.getToken());
                return next.handle(request);
              }),
              catchError((errInner) => {
                if (errInner.code === ApiErrorCode.AUTH_FAIL_INVALID_TOKEN) {
                  this.auth.logOut();
                  return observableEmpty();
                }
                return observableThrowError(errInner);
              }));
          }
          return observableThrowError(err);
        }));
      } else {
        this.auth.logOut();
      }
    }
    return next.handle(request);
  }

  private isInvalidTokenError(err): boolean {
    return err.status === 401 &&
      err.error && err.error.code &&
      ApiErrorCode[ApiErrorCode[err.error.code]] === ApiErrorCode.AUTH_FAIL_INVALID_TOKEN;
  }

  private refreshToken(): Observable<Subscription> {
    const tokenRefreshInProgress = this.refreshTokenInProgress;
    if (tokenRefreshInProgress) {
      return new Observable(observer => {
        this.tokenRefreshed$.subscribe(() => {
          observer.next();
          observer.complete();
        }, err => {
          console.log(err);
        });
      });
    } else {
      this.refreshTokenInProgress = true;
      return new Observable<Subscription>(observer => this.auth.refreshToken()
        .subscribe(() => {
          this.refreshTokenInProgress = false;
          this.tokenRefreshedSource.next();
          observer.next();
          observer.complete();
        }, (err) => {
          observer.error(err);
        }));
    }
  }

  private applyCredentials(request: HttpRequest<any>, token: string) {
    request = request.clone({
      setHeaders: {
        Authorization: `Bearer ${token}`
      }
    });
    return request;
  }
}
