import {Component, Input, OnInit} from '@angular/core';
import {LoadableData} from '../../../loadable-data';
import {Ng2IzitoastService} from 'ng2-izitoast';
import {OwnersService} from '../../owners.service';
import {OwnerLogMessage} from './owner-log-message';

@Component({
  selector: 'app-owner-log',
  templateUrl: './owner-log.component.html',
  styleUrls: ['./owner-log.component.scss']
})
export class OwnerLogComponent implements OnInit {

  @Input('owner') ownerId: string;

  constructor(private ownerService: OwnersService, private iziToast: Ng2IzitoastService) {
  }

  newOwnerLogMessage: string;
  addOwnerLogMessage: LoadableData<OwnerLogMessage[]> = new LoadableData<OwnerLogMessage[]>();
  ownerLogMessages: LoadableData<OwnerLogMessage[]> = new LoadableData<OwnerLogMessage[]>();
  userColors: Map<string, string> = new Map<string, string>();

  ngOnInit() {
    this.ownerLogMessages.start();
    this.ownerService.getOwnerLog(this.ownerId).subscribe(
      data => this.ownerLogMessages.dataReceived(data),
      err => this.ownerLogMessages.errorReceived(err)
    );
  }

  addNewLogEntry() {
    this.addOwnerLogMessage.start();
    if (!this.newOwnerLogMessage || this.newOwnerLogMessage.trim().length == 0) {
      this.addOwnerLogMessage.errorReceived('Write something before saving');
      this.iziToast.error({position: 'topLeft', message: this.addOwnerLogMessage.error});
      return;
    }
    this.ownerService.addOwnerLogEntry(this.ownerId, this.newOwnerLogMessage).subscribe(
      data => {
        this.addOwnerLogMessage.dataReceived(data);
        this.ownerLogMessages.dataReceived(this.addOwnerLogMessage.data.concat(this.ownerLogMessages.data));
        this.newOwnerLogMessage = null;
        this.iziToast.success({position: 'topLeft', message: 'Message saved'});
      },
      err => {
        this.addOwnerLogMessage.errorReceived(err);
        this.iziToast.error({position: 'topLeft', message: this.addOwnerLogMessage.error});
      });
  }

  getUserBgColor(creator: string): string {
    let userColor = this.userColors.get(creator);
    if (!userColor) {
      let noOfExistingColors = this.userColors.size;
      if (noOfExistingColors >= 8) {
        return 'bg_9';
      }
      this.userColors.set(creator, 'bg_' + (noOfExistingColors + 1));
      return this.userColors.get(creator);
    }
    return userColor;
  }
}
