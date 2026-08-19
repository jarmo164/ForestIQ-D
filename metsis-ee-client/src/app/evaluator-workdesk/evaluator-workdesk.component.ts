import {Component, OnInit} from '@angular/core';
import {OwnersService} from '../owners/owners.service';
import {LoadableData} from '../loadable-data';
import {OwnerMinimal} from '../owners/owner-minimal';

@Component({
  selector: 'app-evaluator-workdesk',
  templateUrl: './evaluator-workdesk.component.html',
  styleUrls: ['./evaluator-workdesk.component.scss']
})
export class EvaluatorWorkdeskComponent implements OnInit {

  owners: LoadableData<OwnerMinimal[]> = new LoadableData<OwnerMinimal[]>();

  constructor(private ownersService: OwnersService) {
  }

  ngOnInit() {
    this.owners.start();
    this.ownersService.getOwnersInNeedOfEvaluation().subscribe(
      data => {
        this.owners.dataReceived(data);
      }, err => {
        this.owners.errorReceived(err);
      }
    );
  }

}
