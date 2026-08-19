import {Component, OnDestroy, OnInit} from '@angular/core';
import {RemindersService} from '../reminders/reminders.service';
import {LoadableData} from '../loadable-data';
import {Reminder} from '../reminders/reminder';
import {DateReminders} from './date-reminders';
import {RemindersBucketer} from './reminders-bucketer.service';

@Component({
  selector: 'app-reminders-dashboard',
  templateUrl: './reminders-dashboard.component.html',
  styleUrls: ['./reminders-dashboard.component.scss']
})
export class RemindersDashboardComponent implements OnInit, OnDestroy {

  remindersData: LoadableData<Reminder[]> = new LoadableData<Reminder[]>();
  autoRefresher;
  lastRefreshed: Date = new Date();

  bucketedReminders: DateReminders[];
  userColors: Map<string, string> = new Map<string, string>();

  constructor(
    private remindersService: RemindersService,
    private remindersBucketer: RemindersBucketer
  ) {
  }

  ngOnInit(): void {
    this.remindersData.start();
    if (this.autoRefresher) {
      clearInterval(this.autoRefresher);
    }
    const self = this;
    this.fetchData();
    this.autoRefresher = setInterval(function () {
      console.log('Autorefresh poll activated...');
      self.fetchData();
    }, 60000);

    this.fetchData();
  }

  ngOnDestroy(): void {
    if (this.autoRefresher) {
      clearInterval(this.autoRefresher);
    }
  }

  private fetchData() {
    this.remindersService.getRemindersDashboard().subscribe(
      data => {
        this.remindersData.dataReceived(data);
        this.bucketedReminders = this.remindersBucketer.bucketByDates(data);
        this.lastRefreshed = new Date();
      },
      error => {
        this.remindersData.errorReceived(error);
      }
    );
  }

  isInHour(sd: Date) {
    const today = new Date();
    const someDate = new Date(sd);
    return this.diffMinutes(today, someDate) <= 60;
  }

  private diffMinutes(dt2: Date, dt1: Date): number {
    let diff = (dt2.getTime() - dt1.getTime()) / 1000;
    diff /= 60;
    return Math.abs(Math.round(diff));
  }

  isToday(sd: Date) {
    const today = new Date();
    const someDate = new Date(sd);
    return someDate.getDate() === today.getDate() &&
      someDate.getMonth() === today.getMonth() &&
      someDate.getFullYear() === today.getFullYear();
  }

  isTomorrow(sd: Date) {
    const yesterday = new Date();
    const someDate = new Date(sd);
    yesterday.setDate(yesterday.getDate() + 1);
    return someDate.getDate() === yesterday.getDate() &&
      someDate.getMonth() === yesterday.getMonth() &&
      someDate.getFullYear() === yesterday.getFullYear();
  }

  getUserBgColor(creator: string): string {
    const userColor = this.userColors.get(creator);
    if (!userColor) {
      const noOfExistingColors = this.userColors.size;
      if (noOfExistingColors >= 8) {
        return 'bg_9';
      }
      this.userColors.set(creator, 'bg_' + (noOfExistingColors + 1));
      return this.userColors.get(creator);
    }
    return userColor;
  }
}
