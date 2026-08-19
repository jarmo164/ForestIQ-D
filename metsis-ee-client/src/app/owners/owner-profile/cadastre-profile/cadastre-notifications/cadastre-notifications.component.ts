import {Component, Input, OnInit} from '@angular/core';
import {LoadableData} from "../../../../loadable-data";
import {CadastreNotification} from "./cadastre-notification";
import {OwnersService} from "../../../owners.service";

@Component({
  selector: 'app-cadastre-notifications',
  templateUrl: './cadastre-notifications.component.html',
  styleUrls: ['./cadastre-notifications.component.scss']
})
export class CadastreNotificationsComponent implements OnInit {

  @Input() cadastre: string;

  notifications: LoadableData<CadastreNotification[]> = new LoadableData<CadastreNotification[]>();
  includeArchived = false;

  constructor(private ownersService: OwnersService) { }

  ngOnInit() {
    this.loadNotifications(true);
  }

  loadNotifications(refreshCaches: boolean) {
    this.notifications.start();
    this.ownersService.getCadastreNotifications(this.cadastre, refreshCaches, this.includeArchived).subscribe(
      data => {
        this.notifications.dataReceived(data);
      },
      err => {
        this.notifications.errorReceived(err);
      }
    );
  }

  archivedSelectionChanged() {
    this.loadNotifications(false);
  }

}
