import {Injectable} from '@angular/core';
import {ActivatedRouteSnapshot, CanActivate, Router, RouterStateSnapshot} from '@angular/router';
import {AuthService} from '../auth/auth-service';

@Injectable()
export class MeGuard implements CanActivate {

  constructor(private authService: AuthService, private router: Router) {
  }

  canActivate(next: ActivatedRouteSnapshot,
              state: RouterStateSnapshot): boolean {
    let hasPrivilege = this.authService.isLoggedIn();
    if (!hasPrivilege) {
      this.router.navigate(['/']);
    }
    return hasPrivilege;
  }
}
