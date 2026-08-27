import type { Reminder } from "@/lib/types";

export type ReminderWindow = "OVERDUE" | "NEXT_7_DAYS" | "NEXT_30_DAYS";

export type ReminderOwnerGroup = {
  ownerId: string;
  ownerName: string;
  reminders: Reminder[];
};

export type ReminderAssigneeGroup = {
  assigneeId: string;
  assigneeName: string;
  owners: ReminderOwnerGroup[];
};

export type ReminderDeadlineGroup = {
  dateKey: string;
  dateLabel: string;
  assignees: ReminderAssigneeGroup[];
};

const DAY_MILLISECONDS = 24 * 60 * 60 * 1000;

export function remindersForWindow(
  reminders: Reminder[],
  window: ReminderWindow,
  now = Date.now(),
): Reminder[] {
  const upperBound =
    window === "NEXT_7_DAYS" ? now + 7 * DAY_MILLISECONDS : now + 30 * DAY_MILLISECONDS;

  return reminders
    .filter((reminder) => {
      if (window === "OVERDUE") return reminder.dueTime < now;
      return reminder.dueTime >= now && reminder.dueTime <= upperBound;
    })
    .sort((left, right) => left.dueTime - right.dueTime || left.id.localeCompare(right.id));
}

function localDateKey(value: number): string {
  const date = new Date(value);
  return [date.getFullYear(), String(date.getMonth() + 1).padStart(2, "0"), String(date.getDate()).padStart(2, "0")].join("-");
}

export function deadlineLabel(value: number): string {
  return new Date(value).toLocaleDateString("et-EE", {
    weekday: "long",
    day: "numeric",
    month: "long",
  });
}

function assigneeFor(reminder: Reminder): { id: string; name: string } {
  const assignee = reminder.owner?.assignee;
  if (assignee) return assignee;
  if (reminder.creator) return { id: reminder.creator, name: reminder.creator };
  return { id: "unassigned", name: "Määramata" };
}

function ownerFor(reminder: Reminder): { id: string; name: string } {
  if (reminder.owner) return { id: reminder.owner.id, name: reminder.owner.name };
  return { id: "no-owner", name: "Omanikuta ülesanded" };
}

export function groupRemindersByDeadlineAssigneeAndOwner(
  reminders: Reminder[],
): ReminderDeadlineGroup[] {
  const dates = new Map<string, ReminderDeadlineGroup>();

  for (const reminder of [...reminders].sort((left, right) => left.dueTime - right.dueTime || left.id.localeCompare(right.id))) {
    const dateKey = localDateKey(reminder.dueTime);
    const deadline = dates.get(dateKey) ?? {
      dateKey,
      dateLabel: deadlineLabel(reminder.dueTime),
      assignees: [],
    };
    if (!dates.has(dateKey)) dates.set(dateKey, deadline);

    const assignee = assigneeFor(reminder);
    const assigneeGroup = deadline.assignees.find((group) => group.assigneeId === assignee.id) ?? {
      assigneeId: assignee.id,
      assigneeName: assignee.name,
      owners: [],
    };
    if (!deadline.assignees.includes(assigneeGroup)) deadline.assignees.push(assigneeGroup);

    const owner = ownerFor(reminder);
    const ownerGroup = assigneeGroup.owners.find((group) => group.ownerId === owner.id) ?? {
      ownerId: owner.id,
      ownerName: owner.name,
      reminders: [],
    };
    if (!assigneeGroup.owners.includes(ownerGroup)) assigneeGroup.owners.push(ownerGroup);
    ownerGroup.reminders.push(reminder);
  }

  return Array.from(dates.values());
}
