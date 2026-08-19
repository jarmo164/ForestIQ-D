import {Injectable} from '@angular/core';
import {ActivatedRouteSnapshot, CanActivate, Router, RouterStateSnapshot} from '@angular/router';
import {AuthService} from '../auth/auth-service';

@Injectable()
export class AdminGuard implements CanActivate {

  constructor(private authService: AuthService, private router: Router) {
  }

  canActivate(next: ActivatedRouteSnapshot,
              state: RouterStateSnapshot): boolean {
    const hasPrivilege = this.authService.userHasPrivilege('ADMIN');
    if (!hasPrivilege) {
      this.router.navigate(['/']);
    }
    return hasPrivilege;
  }
}
