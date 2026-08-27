/** ForestIQ Landscape Desk design: quiet Nordic data tooling with crisp operational hierarchy. */
export type Privilege =
  | "ADMIN"
  | "OWNER_PROFILE"
  | "ASSIGNED_OWNERS"
  | "PHONES"
  | "EVALUATION";
export type OrganizationRole =
  | "ORG_OWNER"
  | "ORG_ADMIN"
  | "ORG_MEMBER"
  | "CRM_MANAGER"
  | "EVALUATOR"
  | "CALLER"
  | "VIEWER";
export interface AppUser {
  id: string;
  name: string;
  privileges: Privilege[];
  roles: OrganizationRole[];
  organizationId: string;
}
export interface Owner {
  id: string;
  name: string;
  version: number;
  status?: string | null;
  statusSetAt?: number | null;
  assignee?: { id: string; name: string } | null;
  phone?: string | null;
  email?: string | null;
  address?: string | null;
  info?: string | null;
  type?: string | null;
  cadastres?: Cadastre[];
}
export interface Cadastre {
  id: string;
  name?: string | null;
  marked?: boolean;
  area?: number | null;
  forestArea?: number | null;
  type?: string | null;
  county?: string | null;
  municipality?: string | null;
  address?: string | null;
  labels?: string[];
}
export interface Reminder {
  id: string;
  text: string;
  dueTime: number;
  owner?: Owner | null;
  creator?: string;
  cadastre?: string | null;
  propertyName?: string | null;
}
export interface Message {
  id: string;
  message: string;
  createdAt: number;
  sender?: { id: string; name: string } | null;
  recipient?: { id: string; name: string } | null;
}
export interface OwnerStatus {
  id: string;
  colorHex: string;
  durationDays: number;
  protectedStatus: boolean;
}
export interface Deal {
  id: string;
  version: number;
  owner: Owner;
  saleSubject: "FOREST" | "LAND" | "BOTH";
  stage: string;
  parcels: Cadastre[];
  qualificationNotes?: string | null;
  evaluator?: AppUser | null;
  evaluationStatus?: string | null;
  priceExpectation?: number | null;
  offers: DealOffer[];
  updatedAt?: number | null;
}
export interface DealOffer {
  id: string;
  revision: number;
  kind: string;
  status: string;
  amount: number;
  validUntil?: string | null;
  terms?: string | null;
}
export interface InheritanceCase {
  id: string;
  version: number;
  owner: Owner;
  sourceNoticeNumber?: string | null;
  status: string;
  assignedTo?: AppUser | null;
  certificationDeadline?: string | null;
  heirs: InheritanceHeir[];
  events: InheritanceEvent[];
  updatedAt?: number | null;
}
export interface InheritanceHeir {
  id: string;
  displayName: string;
  phone?: string | null;
  email?: string | null;
  contactStatus?: string | null;
}
export interface InheritanceEvent {
  id: string;
  type: string;
  description: string;
  createdAt: number;
}
export interface SalesTask {
  owner: Owner;
  markedParcelCount: number;
  openDealCount: number;
  nextReminder?: number | null;
}
export interface IntegrationJob {
  key: string;
  label: string;
  configured: boolean;
  lastRun?: {
    id: number;
    status: string;
    finishedAt?: number | null;
    error?: string | null;
  } | null;
}
export interface IntegrationHealth {
  source: string;
  health: "OK" | "DEGRADED";
  lastStatus: string;
  lastSuccessAt: string | null;
  failureStreak: number;
  backlogSize: number;
  lagSeconds: number | null;
}
export interface IntegrationsHealthResponse {
  status: "OK" | "DEGRADED";
  check: "integrations";
  integrations: IntegrationHealth[];
  degradedSources: string[];
}
export interface SyncRun {
  id: number;
  cadastre: string | null;
  taskId: string | null;
  correlationId: string | null;
  source: string;
  status: string;
  pagesProcessed: number;
  rowsProcessed: number;
  retryCount: number;
  backlogSize: number;
  cursor: string;
  lagSeconds: number | null;
  retryOf: number | null;
  startedAt: string | null;
  finishedAt: string | null;
  result: Record<string, unknown>;
  error: string | null;
}
