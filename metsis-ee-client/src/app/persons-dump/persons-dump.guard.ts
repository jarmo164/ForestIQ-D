import { Injectable } from '@angular/core';
import {CanActivate, ActivatedRouteSnapshot, RouterStateSnapshot, Router} from '@angular/router';
import { Observable } from 'rxjs';
import {AuthService} from "../auth/auth-service";

@Injectable()
export class PersonsDumpGuard implements CanActivate {

  constructor(private authService: AuthService, private router: Router) {
  }

  canActivate(
    next: ActivatedRouteSnapshot,
    state: RouterStateSnapshot): Observable<boolean> | Promise<boolean> | boolean {
    let hasPrivilege = this.authService.userHasPrivilege('PHONES');
    if (!hasPrivilege) {
      this.router.navigate(['/']);
    }
    return hasPrivilege;
  }
}
