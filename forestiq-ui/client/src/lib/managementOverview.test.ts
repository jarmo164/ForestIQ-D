import { describe, expect, it } from "vitest";

import {
  filterSalesInterventions,
  filterSalesTeam,
  interventionLabel,
  type SalesIntervention,
  type SalesTeamMember,
} from "./managementOverview";

const team: SalesTeamMember[] = [
  { member: { id: "mari", name: "Mari Müük" }, workload: { assignedOwners: 2, activeDeals: 1, evaluationDeals: 0, overdueReminders: 1 }, contactOutcomes: {}, deals: {} },
  { member: { id: "taavi", name: "Taavi Tehing" }, workload: { assignedOwners: 1, activeDeals: 2, evaluationDeals: 1, overdueReminders: 0 }, contactOutcomes: {}, deals: {} },
];

const interventions: SalesIntervention[] = [
  { kind: "OVERDUE_REMINDER", reminderId: "1", ownerId: "owner-a", ownerName: "Aino Mets", assigneeId: "mari", dueAt: "2026-08-20T10:00:00+00:00" },
  { kind: "EXPIRED_OFFER", dealId: "2", ownerId: "owner-b", ownerName: "Peeter Puu", assigneeId: "taavi", dueAt: "2026-08-21" },
  { kind: "UNASSIGNED_EVALUATION", dealId: "3", ownerId: "owner-c", ownerName: "Kati Kask", assigneeId: null, dueAt: null },
];

describe("sales management filters", () => {
  it("filters team workload by selected member without altering the all-members view", () => {
    expect(filterSalesTeam(team, "ALL")).toEqual(team);
    expect(filterSalesTeam(team, "taavi").map((member) => member.member.name)).toEqual(["Taavi Tehing"]);
  });

  it("filters interventions by both responsible member and intervention type", () => {
    expect(filterSalesInterventions(interventions, "mari", "ALL").map((item) => item.kind)).toEqual(["OVERDUE_REMINDER"]);
    expect(filterSalesInterventions(interventions, "ALL", "EXPIRED_OFFER").map((item) => item.ownerId)).toEqual(["owner-b"]);
    expect(filterSalesInterventions(interventions, "taavi", "OVERDUE_REMINDER")).toEqual([]);
  });

  it("uses human-readable intervention labels", () => {
    expect(interventionLabel("UNASSIGNED_EVALUATION")).toBe("Hindaja määramata");
  });
});
