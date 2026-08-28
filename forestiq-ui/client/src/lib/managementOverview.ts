export type ManagementUser = {
  id: string;
  name: string;
};

export type DashboardStats = {
  activeOwners: number;
  newLeads: number;
  evaluationPending: number;
  deadlines: {
    overdue: number;
    nextSevenDays: number;
    reminders: { overdue: number; nextSevenDays: number };
    inheritance: { overdue: number; nextSevenDays: number };
    offers: { overdue: number; nextSevenDays: number };
  };
  dealStages: Record<string, number>;
  generatedAt: string;
};

export type SalesTeamMember = {
  member: ManagementUser;
  workload: {
    assignedOwners: number;
    activeDeals: number;
    evaluationDeals: number;
    overdueReminders: number;
  };
  contactOutcomes: Record<string, number>;
  deals: Record<string, number>;
};

export type SalesIntervention = {
  kind: "UNASSIGNED_EVALUATION" | "EXPIRED_OFFER" | "OVERDUE_REMINDER";
  dealId?: string;
  reminderId?: string;
  ownerId: string;
  ownerName: string;
  assigneeId?: string | null;
  dueAt: string | null;
};

export type SalesManagementOverview = {
  period: {
    contactOutcomesSince: number;
    generatedAt: number;
  };
  team: SalesTeamMember[];
  interventions: SalesIntervention[];
};

export function filterSalesTeam(
  team: SalesTeamMember[],
  memberId: string,
): SalesTeamMember[] {
  return memberId === "ALL" ? team : team.filter((member) => member.member.id === memberId);
}

export function filterSalesInterventions(
  interventions: SalesIntervention[],
  memberId: string,
  kind: string,
): SalesIntervention[] {
  return interventions.filter((intervention) => {
    const memberMatches = memberId === "ALL" || intervention.assigneeId === memberId;
    const kindMatches = kind === "ALL" || intervention.kind === kind;
    return memberMatches && kindMatches;
  });
}

export function interventionLabel(kind: SalesIntervention["kind"]): string {
  return {
    UNASSIGNED_EVALUATION: "Hindaja määramata",
    EXPIRED_OFFER: "Pakkumine aegunud",
    OVERDUE_REMINDER: "Meeldetuletus hilinenud",
  }[kind];
}
