import {Reminder} from '../reminders/reminder';

export class DateReminders {
  constructor(public date: string, public reminders: Reminder[]) {
  }
}
