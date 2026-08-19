import {ChangeDetectorRef, Component, OnInit} from '@angular/core';
import {PasswordAuthModel} from '../auth/password-auth-model';
import {AuthService} from '../auth/auth-service';
import {DecomposedTotpToken} from './decomposed-totp-token';
import {LoadableData} from '../loadable-data';
import {TotpAuthModel} from '../auth/totp-auth-model';

@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.scss']
})
export class HomeComponent implements OnInit {

  passwordAuthModel: PasswordAuthModel = new PasswordAuthModel();
  pwAuth: LoadableData<DecomposedTotpToken> = new LoadableData<DecomposedTotpToken>();
  totpAuthModel: TotpAuthModel = new TotpAuthModel();
  totpAuth: LoadableData<any> = new LoadableData<any>();

  constructor(public authService: AuthService, private cdr: ChangeDetectorRef) {
  }

  ngOnInit() {
  }

  submitPasswordauth(model) {
    this.pwAuth.start();
    this.authService.doPasswordAuth(model).subscribe(data => {
      this.pwAuth.dataReceived(data);
      setTimeout(function () {
        let totpInput = document.getElementById('totp2');
        if (totpInput == null) {
          totpInput = document.getElementById('totp1');
        }
        if (totpInput != null) {
          totpInput.focus();
        }
      }, 10);
    }, err => this.pwAuth.errorReceived(err));
  }

  submitTotpLogin(model) {
    this.submitTotp(model);
  }

  submitTotpRegister(model) {
    this.submitTotp(model);
  }

  totpQrCodeUrl(): string {
    return 'https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=' +
      encodeURIComponent(this.totpUri());
  }

  private totpUri(): string {
    const user = this.pwAuth.data.userId + '@MetsIS-EE';
    return 'otpauth://totp/' + encodeURIComponent(user) +
      '?secret=' + encodeURIComponent(this.pwAuth.data.totpSecret) +
      '&issuer=' + encodeURIComponent('MetsIS-EE');
  }

  submitTotp(model: TotpAuthModel) {
    this.totpAuth.start();
    this.cdr.detectChanges();
    this.authService.doTotpAuth(model, this.pwAuth.data.token).subscribe(
      () => {
        this.resetAllForms();
      },
      err => {
        this.resetAllForms();
        this.pwAuth.errorReceived(err);
      }
    );
  }

  private resetAllForms() {
    this.totpAuth.reset();
    this.pwAuth.reset();
    this.passwordAuthModel = new PasswordAuthModel();
    this.totpAuthModel = new TotpAuthModel();
  }

}
