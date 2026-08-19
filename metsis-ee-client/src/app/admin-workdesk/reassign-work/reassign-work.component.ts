import {Component, OnInit} from '@angular/core';
import {AdminWorkdeskService} from '../admin-workdesk.service';
import {AdminWorkdeskPreparationData} from '../admin-workdesk-preparation-data';
import {LoadableData} from '../../loadable-data';
import {Ng2IzitoastService} from 'ng2-izitoast';
import {Worksearchcriteria} from '../worksearchcriteria';
import {SelectableOwnerMinimal} from '../selectable-owner-minimal';
import {AssignWorkModel} from '../assign-work-model';

@Component({
  selector: 'app-reassign-work',
  templateUrl: './reassign-work.component.html',
  styleUrls: ['./reassign-work.component.scss']
})
export class ReassignWorkComponent implements OnInit {

  adminWorkdeskPreparationData: LoadableData<AdminWorkdeskPreparationData> = new LoadableData<AdminWorkdeskPreparationData>();
  assignedWorkSearchModel: Worksearchcriteria = new Worksearchcriteria();
  assignedWorkSearch: LoadableData<SelectableOwnerMinimal[]> = new LoadableData<SelectableOwnerMinimal[]>();

  workAssign: LoadableData<any> = new LoadableData<any>();
  workAssignee: string;

  constructor(private adminWorkdeskService: AdminWorkdeskService, private iziToast: Ng2IzitoastService) {
  }

  ngOnInit() {
    this.adminWorkdeskPreparationData.start();
    this.adminWorkdeskService.getPreparationData().subscribe(
      data => {
        this.adminWorkdeskPreparationData.dataReceived(data);
      },
      err => {
        this.adminWorkdeskPreparationData.errorReceived(err);
      }
    );
  }

  doSearch() {
    this.assignedWorkSearch.start();
    if (
      this.assignedWorkSearchModel.status == null &&
      (this.assignedWorkSearchModel.assignees == null || this.assignedWorkSearchModel.assignees.length === 0)
    ) {
      this.assignedWorkSearch.errorReceived('Please choose assignee, status or both.');
      return;
    }
    this.adminWorkdeskService.searchForWork(this.assignedWorkSearchModel).subscribe(
      (data) => {
        this.assignedWorkSearch.dataReceived(data.map(owner => new SelectableOwnerMinimal(owner)));
      },
      err => {
        this.assignedWorkSearch.errorReceived(err);
      }
    );
  }

  reassignWork() {
    this.workAssign.start();
    if (!this.workAssignee) {
      this.workAssign.errorReceived('Assignee not selected.');
      return this.iziToast.error({message: this.workAssign.error, position: 'center'});
    }
    const owners: string[] = [];
    const selectableOwners = this.assignedWorkSearch.data;
    for (let i = 0; i < selectableOwners.length; i++) {
      if (selectableOwners[i].selected) {
        owners.push(selectableOwners[i].id);
      }
    }
    if (owners.length === 0) {
      this.workAssign.errorReceived('Select at least one owner before proceeding.');
      return this.iziToast.error({message: this.workAssign.error, position: 'center'});
    }

    const assignWorkModel = new AssignWorkModel(owners, this.workAssignee, true);
    this.adminWorkdeskService.assignWork(assignWorkModel).subscribe(
      () => {
        this.workAssign.reset();
        this.doSearch();
        this.iziToast.success({message: 'Selected work is reassigned. Rerunning search.', position: 'center'});
      },
      err => {
        this.workAssign.errorReceived(err);
        this.iziToast.error({message: this.workAssign.error, position: 'center'});
      }
    );
  }

}
