import {Component, Input, OnInit} from '@angular/core';
import {AuthService} from '../../../auth/auth-service';
import {LoadableData} from '../../../loadable-data';
import {OwnerStatusData} from './owner-status-data';
import {OwnersService} from '../../owners.service';
import {ChangeOwnerStatusModel} from '../../../admin-workdesk/change-owner-status-model';
import {Ng2IzitoastService} from 'ng2-izitoast';
import {NewReminder} from "../../../reminders/new-reminder";
import {RemindersService} from "../../../reminders/reminders.service";

@Component({
  selector: 'app-owner-status',
  templateUrl: './owner-status.component.html',
  styleUrls: ['./owner-status.component.scss']
})
export class OwnerStatusComponent implements OnInit {

  @Input() ownerId: string;

  status: LoadableData<OwnerStatusData> = new LoadableData<OwnerStatusData>();
  changeOwnerStatus: LoadableData<any> = new LoadableData<any>();
  assigneeChange: LoadableData<any> = new LoadableData<any>();
  changeOwnerStatusModel = new ChangeOwnerStatusModel();
  newAssignee: string;

  newReminder: NewReminder;
  minRemindersDate: Date = new Date();
  reminderAdder: LoadableData<any> = new LoadableData<any>();


  constructor(private ownersService: OwnersService, private remindersService: RemindersService, public authService: AuthService, private iziToast: Ng2IzitoastService) {
  }

  ngOnInit() {
    this.reload();
  }

  reload() {
    this.newReminder = new NewReminder();
    this.newReminder.owner.id = this.ownerId;
    this.minRemindersDate = new Date();

    this.status.start();
    this.ownersService.getStatusData(this.ownerId).subscribe(
      data => {
        this.status.dataReceived(data);
      },
      err => {
        this.status.errorReceived(err);
      }
    );
  }

  doChangeOwnerStatus() {
    this.changeOwnerStatus.start();
    if (!this.changeOwnerStatusModel.newStatus) {
      return this.changeOwnerStatus.errorReceived('Please choose new status.');
    }
    this.ownersService.changeOwnerStatus(this.ownerId, this.changeOwnerStatusModel).subscribe(
      () => {
        this.reload();
        this.changeOwnerStatus.dataReceived('OK');
        this.iziToast.success({position: 'topLeft', message: 'Status change saved'});
      },
      err => {
        return this.changeOwnerStatus.errorReceived(err);
      }
    );
  }

  doChangeAssignee() {
    console.log(this.newAssignee);
    this.assigneeChange.start();
    if (!this.newAssignee) {
      return this.assigneeChange.errorReceived('Please choose new assignee.');
    }
    this.ownersService.changeOwnerAssignee(this.ownerId, this.newAssignee).subscribe(
      () => {
        this.reload();
        this.assigneeChange.dataReceived('OK');
        this.iziToast.success({position: 'topLeft', message: 'Assignee changed'});
      },
      err => {
        return this.assigneeChange.errorReceived(err);
      }
    );
  }

  addReminder() {
    this.reminderAdder.start();
    this.remindersService.submitNewReminder(this.newReminder).subscribe(
      () => {
        this.reload();
        this.reminderAdder.dataReceived('OK');
        this.iziToast.success({
          position: 'topLeft',
          message: 'Reminder added. You can view it in "Reminders" subsection or in this owners "Log" view'
        });
      }, err => {
        this.reminderAdder.errorReceived(err);
        this.iziToast.error({position: 'topLeft', message: this.reminderAdder.error});
      }
    );
  }
}
