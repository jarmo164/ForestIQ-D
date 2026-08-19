import {Component, Input, OnInit} from '@angular/core';
import {BehaviorSubject} from 'rxjs';
import {Message} from '../message';
import {MessagesService} from '../messages.service';
import {Ng2IzitoastService} from 'ng2-izitoast';
import {NewDirectMessage} from '../new-direct-message';

@Component({
  selector: 'app-outgoing-messages',
  templateUrl: './outgoing-messages.component.html',
  styleUrls: ['./outgoing-messages.component.scss']
})
export class OutgoingMessagesComponent implements OnInit {
  messages: BehaviorSubject<Message[]> = new BehaviorSubject<Message[]>([]);

  @Input()
  fullView: boolean;

  @Input()
  numberOfMessages: number;

  pageNo = 1;
  usersLoading = true;
  users = [];
  checkedUserNames;
  messageText: string;

  constructor(private messagesService: MessagesService, private iziToast: Ng2IzitoastService) { }

  ngOnInit(): void {
    this.toTheBeginning();
    this.fetchUsernames();
  }

  private fetchUsernames() {
    this.checkedUserNames = {};
    this.usersLoading = true;
    this.messagesService.getUserNames().subscribe(
      data => {
        this.users = data;
        this.users.forEach(user => {
          this.checkedUserNames[user] = false;
        });
        this.usersLoading = false;
      },
      error => {
        this.iziToast.error({message: error});
      }
     );
  }

  private fetchMessages() {
    this.messages.next([]);
    this.messagesService.getSentMessages(this.pageNo, this.numberOfMessages).subscribe(data => {
      this.messages.next(data);
    }, error => {
      this.iziToast.error({message: error});
    });
  }

  nextPage() {
    this.pageNo++;
    this.fetchMessages();
  }

  toTheBeginning() {
    this.pageNo = 1;
    this.fetchMessages();
  }

  sendMessage() {
    const recipients = Object.keys(this.checkedUserNames).filter(un => this.checkedUserNames[un]);
    if (recipients.length === 0) {
      return this.iziToast.error({message: 'Choose at least one recipient.'});
    }

    const text = this.messageText;
    if (!text) {
      return this.iziToast.error({message: 'Write something before sending a message.'});
    }

    const m = new NewDirectMessage(text, recipients);
    this.messagesService.sendDirectMessage(m).subscribe(
      () => {
        this.messageText = '';
        this.fetchUsernames();
        this.toTheBeginning();
        this.iziToast.success({message: 'Message sent'});
      },
      error => {
        this.toTheBeginning();
        this.iziToast.error({message: 'Failed to send the message. ' + JSON.stringify(error)});
      }
    );
  }
}
