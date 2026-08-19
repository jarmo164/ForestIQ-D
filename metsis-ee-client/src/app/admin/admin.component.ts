import { Component, OnInit } from '@angular/core';
import {WebSocketSubject} from "rxjs/observable/dom/WebSocketSubject";

@Component({
  selector: 'app-admin',
  templateUrl: './admin.component.html',
  styleUrls: ['./admin.component.scss']
})
export class AdminComponent implements OnInit {

  tabs = {
    MAINTAIN_USERS: 0,
    USER_STATISTICS: 1,
    OWNER_STATUSES: 2
  };

  tab: number;

  constructor() {
  }

  ngOnInit() {
    this.showTab(this.tabs.MAINTAIN_USERS);
  }

  showTab(tab: number) {
    this.tab = tab;
  }
}
