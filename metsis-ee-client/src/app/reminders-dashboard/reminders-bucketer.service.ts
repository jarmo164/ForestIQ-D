import {Injectable} from '@angular/core';
import {Reminder} from '../reminders/reminder';
import {DateReminders} from './date-reminders';

@Injectable({
  providedIn: 'root'
})
export class RemindersBucketer {

  constructor() {
  }

  public bucketByDates(reminders: Reminder[]): DateReminders[] {
    const mapped = reminders
      .sort((a, b) => (a.dueTime as unknown as number) - (b.dueTime as unknown as number))
      .map(r => new DateReminders(
        new Date(r.dueTime).toLocaleDateString(
          'en-US',
          {weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'}
        ),
        [r]
        )
      );
    const bucketed: DateReminders[] = [];
    mapped.forEach(m => {
      const idx = bucketed.findIndex(x => m.date === x.date);

      if (idx > -1) {
        bucketed[idx].reminders.push(m.reminders[0]);
      } else {
        bucketed.push(m);
      }
    });

    return bucketed;
  }
}
