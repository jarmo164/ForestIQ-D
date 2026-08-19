import {Component, OnInit} from '@angular/core';
import {LoadableData} from '../loadable-data';
import {OwnerMinimal} from './owner-minimal';
import {OwnerSearchCriteria} from './owner-search-criteria';
import {OwnersService} from './owners.service';

@Component({
  selector: 'app-owners',
  templateUrl: './owners.component.html',
  styleUrls: ['./owners.component.scss']
})
export class OwnersComponent implements OnInit {

  ownersSearch: LoadableData<OwnerMinimal[]> = new LoadableData<OwnerMinimal[]>();
  ownersSearchCriteria: OwnerSearchCriteria = new OwnerSearchCriteria(null, null, null, null, null);
  showAddOwner = null;

  constructor(private ownersService: OwnersService) {
  }

  ngOnInit() {
  }

  searchOwners(criteria: OwnerSearchCriteria) {
    this.ownersSearch.start();
    this.showAddOwner = null;
    this.ownersService.searchOwners(criteria).subscribe(
      owners => {
        this.ownersSearch.dataReceived(owners);
        if (owners == null || owners.length === 0) {
          if (this.ownersSearchCriteria.hasOnlyId()) {
            this.showAddOwner = this.ownersSearchCriteria.id;
          }
        }
      },
      err => this.ownersSearch.errorReceived(err)
    );
  }
}
