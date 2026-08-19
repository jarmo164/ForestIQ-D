import {Component, Input, OnInit} from '@angular/core';
import {RemindersService} from './reminders.service';
import {LoadableData} from '../loadable-data';
import {Reminder} from './reminder';
import {NewReminder} from './new-reminder';
import {Ng2IzitoastService} from 'ng2-izitoast';

@Component({
  selector: 'app-reminders',
  templateUrl: './reminders.component.html',
  styleUrls: ['./reminders.component.scss']
})
export class RemindersComponent implements OnInit {

  reminders: LoadableData<Reminder[]> = new LoadableData<Reminder[]>();

  newReminder: NewReminder = new NewReminder();

  newReminderSubmitter: LoadableData<any> = new LoadableData<any>();

  minRemindersDate = new Date();

  @Input()
  simple: boolean;

  constructor(private remindersService: RemindersService, private iziToast: Ng2IzitoastService) {
  }

  ngOnInit() {
    this.loadMyReminders();
  }

  private loadMyReminders() {
    this.remindersService.getReminders().subscribe(
      data => {
        this.reminders.dataReceived(data);
      },
      err => {
        this.reminders.errorReceived(err);
      }
    );
  }

  submitReminder() {
    this.newReminderSubmitter.start();
    this.remindersService.submitNewReminder(this.newReminder).subscribe(
      data => {
        this.newReminderSubmitter.dataReceived(data);
        this.newReminder = new NewReminder();
        this.loadMyReminders();
      }, err => {
        this.newReminderSubmitter.errorReceived(err);
      });
  }

  deleteReminder(id: number) {
    this.remindersService.deleteReminder(id).subscribe(() => {
      this.iziToast.success({message: 'Reminder deleted'});
      this.loadMyReminders();
    }, err => {
      const ld = new LoadableData();
      ld.errorReceived(err);
      this.iziToast.error({message: ld.error});
    });
  }

  isPastDueTime(reminder: Reminder) {
    return reminder.dueTime <= new Date();
  }

  isDueTimeToday(reminder: Reminder) {
    if (this.isPastDueTime(reminder)) {
      return false;
    }
    const now = new Date();
    const dueTime = new Date(reminder.dueTime);
    return now.getDate() == dueTime.getDate() && now.getMonth() == dueTime.getMonth() && now.getFullYear() == dueTime.getFullYear();
  }
}
