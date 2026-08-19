import {Injectable} from '@angular/core';
import {HttpClient, HttpHeaders} from '@angular/common/http';
import {Observable} from 'rxjs';
import {ApiErrorHandler} from '../api-error-handler';
import {catchError, map} from 'rxjs/operators';
import {PasswordAuthModel} from './password-auth-model';
import {JwtHelperService} from '@auth0/angular-jwt';
import {DecomposedTotpToken} from '../home/decomposed-totp-token';
import {EncodedToken} from './encoded-token';
import {TotpAuthModel} from './totp-auth-model';
import {EncodedTokens} from './encoded-tokens';
import {AppUser} from './app-user';

import {Router} from '@angular/router';
import {ChangeMyPasswordModel} from './change-my-password-model';
import {OwnerLogMessage} from '../owners/owner-profile/owner-log/owner-log-message';

@Injectable()
export class AuthService {

  constructor(
    private http: HttpClient,
    private errors: ApiErrorHandler,
    private jwtHelperService: JwtHelperService,
    private router: Router
  ) {
  }

  doPasswordAuth(model: PasswordAuthModel): Observable<DecomposedTotpToken> {
    return this.http.post<EncodedToken>('api/password-login', {},
      {
        headers: new HttpHeaders({
          'Authorization': 'Basic ' + btoa((model.userId || '') + ':' + (model.password || ''))
        })
      }).pipe(map(data => {
      const token = data.token;
      const decodedToken = this.jwtHelperService.decodeToken(token);
      return new DecomposedTotpToken(decodedToken.userId, decodedToken.userName, decodedToken.totpsecret, token);
    })).pipe(catchError(this.errors.handle));
  }

  doTotpAuth(totpAuthModel: TotpAuthModel, totpToken: string) {
    return this.http.post<EncodedTokens>(
      'api/services/totp', totpAuthModel, {headers: new HttpHeaders({'Authorization': 'Bearer ' + totpToken})})
      .pipe(map(tokens => {
        this.setTokens(tokens);
        return 'OK';
      }))
      .pipe(catchError(this.errors.handle));
  }

  changeMyPassword(model: ChangeMyPasswordModel): Observable<any> {
    return this.http.post<EncodedTokens>('api/services/change-my-password', model).pipe(catchError(this.errors.handle));
  }

  isLoggedIn() {
    if (this.jwtHelperService.isTokenExpired()) {
      if (this.jwtHelperService.isTokenExpired(this.getRefreshToken())) {
        this.logOut();
        return false;
      }
    }
    return true;
  }

  isFullScreenPage() {
    const url = this.router.url;
    return url.indexOf('reminders-dashboard') > -1;
  }

  getLoggedInUser(): AppUser {
    if (!this.isLoggedIn()) {
      return null;
    }
    const decodedToken = this.jwtHelperService.decodeToken();
    return new AppUser(decodedToken.userId, decodedToken.userName, decodedToken.privileges);
  }

  userHasPrivilege(privilegeId: string): boolean {
    if (!this.isLoggedIn()) {
      return false;
    }
    return this.getLoggedInUser().privileges.indexOf(privilegeId) >= 0;
  }

  getToken(): string {
    return localStorage.getItem('auth_token');
  }

  private setTokens(tokens: EncodedTokens) {
    localStorage.setItem('auth_token', tokens.actualToken.token);
    localStorage.setItem('refresh_token', tokens.refreshToken.token);
  }

  logOut() {
    if (this.getToken() != null || this.getRefreshToken() != null) {
      this.removeTokens();
      this.router.navigate(['/']);
    }
  }

  private removeTokens() {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('refresh_token');
  }

  getRefreshToken(): string {
    return localStorage.getItem('refresh_token');
  }

  refreshToken(): Observable<string> {
    const refreshToken = this.getRefreshToken();
    console.log('Calling api/services/token-refresh with refresh token ' + refreshToken +
      '. Auth token is at the same time: ' + this.getToken());
    return this.http.post<EncodedTokens>('api/services/token-refresh',
      {}, {headers:
          new HttpHeaders({'Authorization': 'Bearer ' + refreshToken})})
      .pipe(map(tokens => {
        this.setTokens(tokens);
        return 'OK';
      })).pipe(catchError(this.errors.handle));
  }

  // just to force token refresh for example
  doDummyRequest(): Observable<any> {
    return this.http.get<OwnerLogMessage[]>('api/services/status').pipe(catchError(this.errors.handle));
  }
}
