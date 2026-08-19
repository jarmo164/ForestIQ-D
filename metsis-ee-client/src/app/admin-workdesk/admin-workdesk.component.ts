import {Component, OnInit} from '@angular/core';

@Component({
  selector: 'app-admin-workdesk',
  templateUrl: './admin-workdesk.component.html',
  styleUrls: ['./admin-workdesk.component.scss']
})
export class AdminWorkdeskComponent implements OnInit {

  tabs = {
    SEARCH_FOR_WORK: 0,
    REASSIGN_OWNERS: 1
  };

  tab: number;

  ngOnInit(): void {
    this.showTab(this.tabs.SEARCH_FOR_WORK);
  }

  showTab(tab: number) {
    this.tab = tab;
  }
}
