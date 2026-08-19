import { Component, OnInit } from '@angular/core';
import {LoadableData} from "../../loadable-data";
import {OwnerStatus} from "../../owners/owner-status-bubble/owner-status";
import {AdminService} from "../admin.service";
import {Ng2IzitoastService} from "ng2-izitoast";

@Component({
  selector: 'app-maintain-owner-statuses',
  templateUrl: './maintain-owner-statuses.component.html',
  styleUrls: ['./maintain-owner-statuses.component.scss']
})
export class MaintainOwnerStatusesComponent implements OnInit {

  ownerStatuses: LoadableData<OwnerStatus[]> = new LoadableData<OwnerStatus[]>();
  newStatus: OwnerStatus = this.initNewStatus();

  constructor(private adminService: AdminService, private iziToast: Ng2IzitoastService) { }

  ngOnInit() {
    this.reloadExistingOwnerStatuses();
  }

  private reloadExistingOwnerStatuses() {
    this.ownerStatuses.start();
    this.adminService.getAllOwnerStatuses().subscribe(
      data => {
        this.ownerStatuses.dataReceived(data);
      },
      err => {
        this.ownerStatuses.errorReceived(err);
      }
    );
  }

  saveStatus(status: OwnerStatus) {
    this.ownerStatuses.start();
    this.adminService.saveOwnerStatus(status).subscribe(
      () => {
        this.iziToast.success({message: 'Saved all changes', position: 'center'});
        this.reloadExistingOwnerStatuses();
      },
      err => {
        this.ownerStatuses.errorReceived(err);
        this.iziToast.error({message: this.ownerStatuses.error, position: 'center'});
        this.reloadExistingOwnerStatuses();
      }
    );
  }

  deleteStatus(id: string) {
    this.ownerStatuses.start();
    this.adminService.deleteOwnerStatus(id).subscribe(
      () => {
        this.iziToast.success({message: 'Deleted status ' + id, position: 'center'});
        this.reloadExistingOwnerStatuses();
      },
      err => {
        this.ownerStatuses.errorReceived(err);
        this.iziToast.error({message: this.ownerStatuses.error, position: 'center'});
        this.reloadExistingOwnerStatuses();
      }
    );
  }

  private initNewStatus(): OwnerStatus {
    return {id: null, colorHex: 'ed7a6f', durationDays: 175, protectedReason: false};
  }

  addNewStatus() {
    this.ownerStatuses.start();
    this.adminService.saveOwnerStatus(this.newStatus).subscribe(
      () => {
        this.iziToast.success({message: 'New status added!'});
        this.reloadExistingOwnerStatuses();
        this.newStatus = this.initNewStatus();
      }, err => {
        this.ownerStatuses.errorReceived(err);
        this.iziToast.error({message: this.ownerStatuses.error, position: 'center'});
        this.reloadExistingOwnerStatuses();
      }
    );
  }
}
