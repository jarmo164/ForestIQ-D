import { Injectable } from '@angular/core';
import {CanActivate, ActivatedRouteSnapshot, RouterStateSnapshot, Router} from '@angular/router';
import {AuthService} from '../auth/auth-service';

@Injectable()
export class OwnersGuard implements CanActivate {
  constructor(private authService: AuthService, private router: Router) {
  }

  canActivate(next: ActivatedRouteSnapshot,
              state: RouterStateSnapshot): boolean {
    let hasPrivilege = this.authService.userHasPrivilege('OWNER_PROFILE');
    if (!hasPrivilege) {
      this.router.navigate(['/']);
    }
    return hasPrivilege;
  }
}
