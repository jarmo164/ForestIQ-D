import {ChangeDetectorRef, Component, OnInit} from '@angular/core';
import {Worksearchcriteria} from '../worksearchcriteria';
import {AdminWorkdeskPreparationData} from '../admin-workdesk-preparation-data';
import {Ng2IzitoastService} from 'ng2-izitoast';
import {LoadableData} from '../../loadable-data';
import {SelectableOwnerMinimal} from '../selectable-owner-minimal';
import {AssignWorkModel} from '../assign-work-model';
import {AdminWorkdeskService} from '../admin-workdesk.service';

@Component({
  selector: 'app-work-search',
  templateUrl: './work-search.component.html',
  styleUrls: ['./work-search.component.scss']
})
export class WorkSearchComponent implements OnInit {


  workSearchResults: LoadableData<SelectableOwnerMinimal[]> = new LoadableData<SelectableOwnerMinimal[]>();
  workSearchCriteria: Worksearchcriteria = new Worksearchcriteria();
  adminWorkdeskPreparationData: LoadableData<AdminWorkdeskPreparationData> = new LoadableData<AdminWorkdeskPreparationData>();


  workAssign: LoadableData<any> = new LoadableData<any>();
  workAssignee: string;
  allResultsChecked = true;

  orderer: {
    field: string,
    order: string
  } = {
    field: 'id',
    order: 'asc'
  };

  constructor(private adminWorkdeskService: AdminWorkdeskService, private iziToast: Ng2IzitoastService, private cdr: ChangeDetectorRef) {
  }

  orderedResults(): SelectableOwnerMinimal[] {
   const data = this.workSearchResults.data;
   if (data == null) {
     return [];
   }
   return data.sort((a: SelectableOwnerMinimal, b: SelectableOwnerMinimal) => {
     const field = this.orderer.field.split('.');

     let aElement = a;
     let bElement = b;
     // tslint:disable-next-line:forin
     for (let i = 0; i < field.length; i++) {
       const f = field[i];
       aElement = aElement[f] || {};
       bElement = bElement[f] || {};
     }
     if (aElement == null) {
       return -1;
     }
     if (bElement == null) {
       return 1;
     }
     if (aElement < bElement) {
        if (this.orderer.order === 'desc') {
          return -1;
        } else {
          return 1;
        }
      }
      if (aElement > bElement) {
        if (this.orderer.order === 'desc') {
          return 1;
        } else {
          return -1;
        }
      }
      return 0;
    });
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

  searchForWork(model: Worksearchcriteria) {
    this.workSearchResults.start();
    this.cdr.detectChanges();
    this.adminWorkdeskService.searchForWork(model).subscribe(
      owners => {
        this.workSearchResults.dataReceived(owners.map(owner => new SelectableOwnerMinimal(owner)));
        this.allResultsChecked = true;
      }, err => {
        this.workSearchResults.errorReceived(err);
      }
    );
  }

  toggleAllResults() {
    this.workSearchResults.data.forEach(o => o.selected = !this.allResultsChecked);
  }

  assignWork() {
    this.workAssign.start();
    if (!this.workAssignee) {
      this.workAssign.errorReceived('Assignee not selected.');
      return this.iziToast.error({message: this.workAssign.error, position: 'center'});
    }
    const owners: string[] = [];
    const selectableOwners = this.workSearchResults.data;
    for (let i = 0; i < selectableOwners.length; i++) {
      if (selectableOwners[i].selected) {
        owners.push(selectableOwners[i].id);
      }
    }
    if (owners.length === 0) {
      this.workAssign.errorReceived('Select at least one owner before proceeding.');
      return this.iziToast.error({message: this.workAssign.error, position: 'center'});
    }

    const assignWorkModel = new AssignWorkModel(owners, this.workAssignee, false);
    this.adminWorkdeskService.assignWork(assignWorkModel).subscribe(
      () => {
        this.workAssign.reset();
        this.searchForWork(this.workSearchCriteria);
        this.iziToast.success({message: 'Selected work is assigned. Rerunning search.', position: 'center'});
      },
      err => {
        this.workAssign.errorReceived(err);
        this.iziToast.error({message: this.workAssign.error, position: 'center'});
      }
    );
  }

  setOrderer(field: string, order: string) {
    this.orderer = {
      field: field,
      order: order
    };
  }
}
