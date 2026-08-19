import {Component, OnInit} from '@angular/core';
import {MyWorkSearchCriteria} from './my-work-search-criteria';
import {LoadableData} from '../loadable-data';
import {OwnerMinimal} from '../owners/owner-minimal';
import {OwnersService} from '../owners/owners.service';
import {Ng2IzitoastService} from "ng2-izitoast";
import {CallerWorkdeskPrepData} from "./caller-workdesk-prep-data";

@Component({
  selector: 'app-caller-wordesk',
  templateUrl: './caller-wordesk.component.html',
  styleUrls: ['./caller-wordesk.component.scss']
})
export class CallerWordeskComponent implements OnInit {

  possibleOwnerStatuses = [];
  myWorkSearchCriteria: MyWorkSearchCriteria = new MyWorkSearchCriteria();
  work: LoadableData<OwnerMinimal[]> = new LoadableData<OwnerMinimal[]>();
  prepData: LoadableData<CallerWorkdeskPrepData> = new LoadableData<CallerWorkdeskPrepData>();

  constructor(private ownersService: OwnersService, private iziToast: Ng2IzitoastService) {
  }

  ngOnInit() {
    this.prepData.start();
    this.ownersService.prepareCallerWorkdesk().subscribe(
      data => {
        data.statuses.forEach(key => {
          this.possibleOwnerStatuses.push({id: key, itemName: key});
        });
        this.myWorkSearchCriteria.statuses = [
          {id: 'ASSIGNED', itemName: 'ASSIGNED'},
          {id: 'EVALUATED_NEEDS_ACTION', itemName: 'EVALUATED_NEEDS_ACTION'},
        ];
        this.prepData.dataReceived(data);
        this.searchMyWork('status_set_at', 'asc');
      },
      err => {
        this.prepData.errorReceived(err);
        this.iziToast.error({message: 'Preparing workdesk failed: ' + this.prepData.error, position: 'topLeft'});
      }
    );
  }

  searchMyWork(order: string, direction: string) {
    this.myWorkSearchCriteria.direction = direction;
    this.myWorkSearchCriteria.order = order;
    this.work.start();
    this.ownersService.searchMyWork(this.myWorkSearchCriteria).subscribe(
      data => {
        this.work.dataReceived(data);
      },
      err => {
        this.work.errorReceived(err);
      }
    );
  }
}
