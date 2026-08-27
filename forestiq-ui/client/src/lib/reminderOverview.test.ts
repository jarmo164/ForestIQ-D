import { describe, expect, it } from "vitest";

import {
  groupRemindersByDeadlineAssigneeAndOwner,
  remindersForWindow,
} from "./reminderOverview";
import type { Reminder } from "./types";

const now = Date.UTC(2026, 7, 27, 10, 0, 0);
const ownerA = {
  id: "79401:001:0001",
  name: "Aino Mets",
  version: 1,
  assignee: { id: "mari", name: "Mari Müük" },
};
const ownerB = {
  id: "79401:001:0002",
  name: "Peeter Puu",
  version: 1,
  assignee: { id: "mari", name: "Mari Müük" },
};

const reminders: Reminder[] = [
  { id: "overdue", text: "Helista tagasi", dueTime: now - 1, owner: ownerA },
  { id: "seven-days", text: "Saada pakkumine", dueTime: now + 7 * 24 * 60 * 60 * 1000, owner: ownerA },
  { id: "thirty-days", text: "Kontrolli tähtaega", dueTime: now + 30 * 24 * 60 * 60 * 1000, owner: ownerB },
  { id: "future", text: "Ei ole veel nähtav", dueTime: now + 31 * 24 * 60 * 60 * 1000, owner: ownerB },
];

describe("reminder deadline overview", () => {
  it("filters overdue, seven-day and thirty-day views using inclusive deadlines", () => {
    expect(remindersForWindow(reminders, "OVERDUE", now).map((reminder) => reminder.id)).toEqual(["overdue"]);
    expect(remindersForWindow(reminders, "NEXT_7_DAYS", now).map((reminder) => reminder.id)).toEqual(["seven-days"]);
    expect(remindersForWindow(reminders, "NEXT_30_DAYS", now).map((reminder) => reminder.id)).toEqual(["seven-days", "thirty-days"]);
  });

  it("groups the active work by deadline, responsible person and owner", () => {
    const grouped = groupRemindersByDeadlineAssigneeAndOwner([
      { id: "later", text: "Teine tegevus", dueTime: now + 60_000, owner: ownerA },
      { id: "first", text: "Esimene tegevus", dueTime: now, owner: ownerA },
      { id: "other-owner", text: "Kolmas tegevus", dueTime: now, owner: ownerB },
    ]);

    expect(grouped).toHaveLength(1);
    expect(grouped[0].assignees).toHaveLength(1);
    expect(grouped[0].assignees[0]).toMatchObject({ assigneeId: "mari", assigneeName: "Mari Müük" });
    expect(grouped[0].assignees[0].owners.map((owner) => owner.ownerName)).toEqual(["Aino Mets", "Peeter Puu"]);
    expect(grouped[0].assignees[0].owners[0].reminders.map((reminder) => reminder.id)).toEqual(["first", "later"]);
  });
});
