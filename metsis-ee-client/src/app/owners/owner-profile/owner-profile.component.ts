import {Component, OnInit} from '@angular/core';
import {OwnersService} from '../owners.service';
import {ActivatedRoute, Params, Router} from '@angular/router';
import {LoadableData} from '../../loadable-data';
import {Owner} from './owner';
import {Ng2IzitoastService} from 'ng2-izitoast';
import {ActiveCadastreService} from './the-map/active-cadastre.service';
import {OwnerId} from './owner-id';
import {AuthService} from '../../auth/auth-service';
import {ConfirmationDialogService} from '../../confirmation-dialog/confirmation-dialog.service';

@Component({
  selector: 'app-owner-profile',
  templateUrl: './owner-profile.component.html',
  styleUrls: ['./owner-profile.component.scss']
})
export class OwnerProfileComponent implements OnInit {

  ownerId: string;
  ownerData: LoadableData<Owner> = new LoadableData<Owner>();
  modifyOwner: LoadableData<any> = new LoadableData<any>();
  ownerInfoVisible = false;
  cadastreListOrder = '-area';
  cadastreMarker: LoadableData<any> = new LoadableData<any>();
  anyOwnerAssignedToMe: LoadableData<OwnerId> = new LoadableData<OwnerId>();
  notificationsEnabled: LoadableData<boolean> = new LoadableData<boolean>();

  visibleOwnerDetailsTab: number;

  addOwnerFormVisible = false;
  addOwnerOwnerName: string;
  addOwnerOwnerType = 'ERAISIK';
  ownerAdder: LoadableData<any> = new LoadableData<any>();
  private showCadastreList = false;

  constructor(private ownersService: OwnersService,
              private router: Router,
              private route: ActivatedRoute,
              private iziToast: Ng2IzitoastService,
              private activeCadastreService: ActiveCadastreService,
              private authService: AuthService,
              private confirmationDialogService: ConfirmationDialogService) {
  }

  ngOnInit(): void {
    this.route.params.subscribe((params: Params) => {
      this.ownerId = params['id'];
      this.initializeOwnerFollowing();
      this.initializeOwner(0);
    });
  }

  private initializeOwnerFollowing() {
    this.notificationsEnabled.start();
    this.ownersService.getOwnerFollowers(this.ownerId).subscribe(
      data => {
        this.notificationsEnabled.dataReceived(data.followers.indexOf(this.authService.getLoggedInUser().userId) > -1);
      }
    );
  }

  addOwner() {
    this.ownerAdder.start();
    this.ownersService.addOwner(this.ownerId, this.addOwnerOwnerName, this.addOwnerOwnerType).subscribe(
      () => {
        window.location.reload();
      },
      err => {
        this.ownerAdder.errorReceived(err);
      }
    );
  }

  ownerGenderClass(): string {
    if (this.ownerData.data.type !== 'ERAISIK') {
      return '';
    }
    const genderChar = this.ownerData.data.id.charAt(0);
    return (genderChar === '3' || genderChar === '5') ? 'owner-man' : ((genderChar === '4' || genderChar === '6') ? 'owner-woman' : '');
  }


  private initializeOwner(tabNo: number) {
    this.showCadastreList = false;
    this.ownerData.start();
    this.activeCadastreService.deactivate();
    this.ownersService.getOwner(this.ownerId).subscribe(
      owner => {
        this.ownerData.dataReceived(owner);
        this.showOwnerTab(tabNo);
      },
      err => {
        if (err.code !== 'OWNER_NOT_FOUND' || !this.authService.userHasPrivilege('OWNER_PROFILE')) {
          return this.ownerData.errorReceived(err);
        } else {
          this.addOwnerFormVisible = true;
        }
      }
    );
  }

  saveChangesOnOwnerInfo(owner) {
    this.modifyOwner.start();
    const ownerClone = Object.assign({}, owner);
    ownerClone.cadastres = null;
    this.ownersService.saveOwnerChanges(ownerClone).subscribe(
      data => {
        this.modifyOwner.dataReceived(data);
        this.iziToast.success({message: 'Owner changes saved', position: 'topLeft'});
      },
      err => {
        this.modifyOwner.errorReceived(err);
        this.iziToast.error({message: this.modifyOwner.error, position: 'topLeft'});
      }
    );
  }

  toggleOwnerInfo() {
    this.ownerInfoVisible = !this.ownerInfoVisible;
  }

  activateCadastre(cadastreNo: string) {
    this.activeCadastreService.activateCadastre(cadastreNo);
  }

  showOwnerTab(tabNo: number) {
    this.showCadastreList = false;
    this.visibleOwnerDetailsTab = tabNo;
  }

  setCadastreListOrder(order: string) {
    this.cadastreListOrder = order;
  }

  markInterestingCadastres() {
    this.cadastreMarker.start();
    const markedCadastres = this.ownerData.data.cadastres.filter(c => c.marked).map(c => c.id);
    this.ownersService.markInterestingCadastres(this.ownerData.data.id, markedCadastres)
      .subscribe(
        () => {
          this.initializeOwner(1);
          this.iziToast.success({position: 'topLeft', message: 'Cadastres marked'});
          this.cadastreMarker.reset();
        }, err => {
          this.cadastreMarker.errorReceived(err);
          this.iziToast.error({position: 'topLeft', message: this.cadastreMarker.error});
        });
  }

  moveToAnyAssignedOwner() {
    this.anyOwnerAssignedToMe.start();
    this.ownersService.getNextOwnerAssignedToMe()
      .subscribe(
        (data) => {
          this.anyOwnerAssignedToMe.dataReceived(data);
          this.router.navigate(['/owners/' + data.ownerId]);
        }, err => {
          this.anyOwnerAssignedToMe.errorReceived(err);
          this.iziToast.error({position: 'topLeft', message: this.anyOwnerAssignedToMe.error});
        });
  }

  doShowCadastreList() {
    return this.showCadastreList = true;
  }

  shouldShowCadastreList() {
    return this.ownerData.data.cadastres.length < 50 || this.showCadastreList === true;
  }

  disableNotifications() {
    this.ownersService.disableOwnerNotifications(this.ownerId, this.authService.getLoggedInUser().userId).subscribe(
      () => {
        this.initializeOwnerFollowing();
      }
    );
  }

  enableNotifications() {
    this.ownersService.enableOwnerNotifications(this.ownerId, this.authService.getLoggedInUser().userId).subscribe(
      () => {
        this.initializeOwnerFollowing();
      }
    );
  }
}

