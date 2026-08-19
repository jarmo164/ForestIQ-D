import {Component, OnInit} from '@angular/core';
import {LoadableData} from '../../../loadable-data';
import {Cadastre} from '../cadastre';
import {OwnersService} from '../../owners.service';
import {ActiveCadastreService} from '../the-map/active-cadastre.service';
import {AuthService} from '../../../auth/auth-service';
import {OwnerMinimal} from '../../owner-minimal';
import {Ng2IzitoastService} from 'ng2-izitoast';

@Component({
  selector: 'app-cadastre-profile',
  templateUrl: './cadastre-profile.component.html',
  styleUrls: ['./cadastre-profile.component.scss']
})
export class CadastreProfileComponent implements OnInit {

  cadastre: LoadableData<Cadastre> = new LoadableData<Cadastre>();
  visibleCadastreDetailsTab: number;

  constructor(private ownersService: OwnersService,
              private activeCadastreService: ActiveCadastreService,
              private authService: AuthService,
              private iziToast: Ng2IzitoastService) {
    this.activeCadastreService.setActivateCadastrePaneFn(this.loadCadastre.bind(this));
    this.activeCadastreService.setUnsetActicveCadastreFromPaneFn(this.closePane.bind(this));
  }

  ngOnInit() {
  }

  loadCadastre(cadastreNo: string) {
    this.cadastre.reset();
    if (cadastreNo) {
      this.cadastre.start();
      this.ownersService.getCadastreDetails(cadastreNo).subscribe(
        cadastreDetails => {
          this.showCadastreTab(0);
          this.cadastre.dataReceived(cadastreDetails);
        }, err => {
          this.cadastre.errorReceived(err);
        });
    }
  }

  showCadastreTab(tabNo: number) {
    this.visibleCadastreDetailsTab = tabNo;
  }

  zoomMapToActiveCadastre() {
    this.activeCadastreService.zoomToActive();
  }

  zoomMapToEstonia() {
    this.activeCadastreService.zoomToEstonia();
  }

  iAmAllowedToViewOwner(owner: OwnerMinimal): boolean {
    let loggedInUser = this.authService.getLoggedInUser();
    if (loggedInUser.privileges.indexOf('OWNER_PROFILE') >= 0) {
      return true;
    }
    return (!!owner.assignee) && owner.assignee.id == loggedInUser.userId;

  }

  private closePane(){
    this.cadastre.reset();
  }

  close() {
    this.activeCadastreService.deactivate();
  }

  copyToClipboard(id: string) {
    const el = document.createElement('textarea');
    el.value = id;
    document.body.appendChild(el);
    el.select();
    document.execCommand('copy');
    document.body.removeChild(el);
    this.iziToast.success({position: 'topRight', message: 'Copied ' + id + ' to clipboard.'});
  }
}
