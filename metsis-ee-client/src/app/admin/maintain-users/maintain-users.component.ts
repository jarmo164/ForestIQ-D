import {Component, OnInit} from '@angular/core';
import {MaintainableUser} from './maintainable-user';
import {LoadableData} from '../../loadable-data';
import {AdminService} from '../admin.service';
import {Ng2IzitoastService} from 'ng2-izitoast';
import {AddUserResponse} from '../add-user-response';
import {ConfirmationDialogService} from '../../confirmation-dialog/confirmation-dialog.service';

@Component({
  selector: 'app-maintain-users',
  templateUrl: './maintain-users.component.html',
  styleUrls: ['./maintain-users.component.scss']
})
export class MaintainUsersComponent implements OnInit {

  userAddModel = new MaintainableUser(null, null, null);
  addableUser: LoadableData<AddUserResponse> = new LoadableData<AddUserResponse>();
  maintainableUsers: LoadableData<MaintainableUser[]> = new LoadableData<MaintainableUser[]>();

  constructor(private adminService: AdminService, private iziToast: Ng2IzitoastService, private confirmationDialogService: ConfirmationDialogService) {
  }

  ngOnInit() {
    this.reloadMaintainableUsers();
  }

  private reloadMaintainableUsers() {
    this.maintainableUsers.start();
    this.adminService.getAllMaintainableUsers().subscribe(
      data => {
        this.maintainableUsers.dataReceived(data);
      },
      err => {
        this.maintainableUsers.errorReceived(err);
      }
    );
  }

  confirmDeleteUser(user: MaintainableUser) {
    this.confirmationDialogService.confirm('Are you sure?', 'Do you really want to delete user ' + user.name + '?')
      .then((confirmed) => {
        if (confirmed) {
          this.deleteUser(user);
        }
      });
  }

  deleteUser(user: MaintainableUser) {
    this.adminService.deleteUser(user).subscribe(
      () => {
        this.iziToast.success({message: 'User  "' + user.name + '" deleted'});
        this.reloadMaintainableUsers();
      }, err => {
        this.iziToast.error({message: err});
      }
    );
  }

  savePrivileges(user: MaintainableUser) {
    this.adminService.setUserPrivileges(user).subscribe(
      () => {
        this.iziToast.success({message: 'Privileges saved for user "' + user.name + '"'});
        this.reloadMaintainableUsers();
      }, err => {
        this.iziToast.error({message: err});
      }
    );
  }

  addUser(user: MaintainableUser) {
    this.addableUser.start();
    this.adminService.addUser(user).subscribe(data => {
      this.addableUser.dataReceived(data);
      this.reloadMaintainableUsers();
    }, err => {
      this.addableUser.errorReceived(err);
    });
  }

}
