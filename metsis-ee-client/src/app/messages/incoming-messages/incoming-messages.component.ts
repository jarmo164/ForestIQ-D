import {Component, Input, OnInit} from '@angular/core';
import {BehaviorSubject} from 'rxjs';
import {Message} from '../message';
import {MessagesService} from '../messages.service';
import {Ng2IzitoastService} from 'ng2-izitoast';

@Component({
  selector: 'app-incoming-messages',
  templateUrl: './incoming-messages.component.html',
  styleUrls: ['./incoming-messages.component.scss']
})
export class IncomingMessagesComponent implements OnInit {

  incomingMessages: BehaviorSubject<Message[]> = new BehaviorSubject<Message[]>([]);

  @Input()
  fullView: boolean;

  @Input()
  numberOfMessages: number;

  pageNo = 1;

  constructor(private messagesService: MessagesService, private iziToast: Ng2IzitoastService) { }

  ngOnInit(): void {
    this.fetchMessages();
  }

  private fetchMessages() {
    this.incomingMessages.next([]);
    this.messagesService.getReceivedMessages(this.pageNo, this.numberOfMessages).subscribe(data => {
      this.incomingMessages.next(data);
    }, error => {
      this.iziToast.error({message: error});
    });
  }

  nextPage() {
    this.pageNo++;
    this.fetchMessages();
  }

  firstPage() {
    this.pageNo = 1;
    this.fetchMessages();
  }

  markAllAsRead() {
    const currentState = this.incomingMessages.getValue();
    if (currentState.length !== 0) {
      const newestMessageDate = currentState[0].createdAt;
      if (newestMessageDate) {
        this.messagesService.markAllReceicedAsRead(newestMessageDate).subscribe(() => {
          this.firstPage();
        }, error => {
          this.iziToast.error({message: error});
        });
      }
    } else {
      this.firstPage();
    }
  }
}
