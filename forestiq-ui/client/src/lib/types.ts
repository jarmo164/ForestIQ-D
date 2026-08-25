/** ForestIQ Landscape Desk design: quiet Nordic data tooling with crisp operational hierarchy. */
export type Privilege = "ADMIN" | "OWNER_PROFILE" | "ASSIGNED_OWNERS" | "PHONES" | "EVALUATION";
export interface AppUser { id: string; name: string; privileges: Privilege[]; }
export interface Owner { id: string; name: string; status?: string | null; statusSetAt?: number | null; assignee?: { id: string; name: string } | null; phone?: string | null; email?: string | null; address?: string | null; info?: string | null; type?: string | null; cadastres?: Cadastre[]; }
export interface Cadastre { id: string; name?: string | null; marked?: boolean; area?: number | null; forestArea?: number | null; type?: string | null; county?: string | null; municipality?: string | null; address?: string | null; labels?: string[]; }
export interface Reminder { id: string; text: string; dueTime: number; owner?: Owner | null; creator?: string; }
export interface Message { id: string; message: string; createdAt: number; sender?: { id: string; name: string } | null; recipient?: { id: string; name: string } | null; }
export interface OwnerStatus { id: string; colorHex: string; durationDays: number; protectedStatus: boolean; }
export interface Deal { id: string; owner: Owner; saleSubject: "FOREST" | "LAND" | "BOTH"; stage: string; parcels: Cadastre[]; qualificationNotes?: string | null; evaluator?: AppUser | null; evaluationStatus?: string | null; priceExpectation?: number | null; offers: DealOffer[]; updatedAt?: number | null; }
export interface DealOffer { id: string; revision: number; kind: string; status: string; amount: number; validUntil?: string | null; terms?: string | null; }
export interface InheritanceCase { id: string; owner: Owner; sourceNoticeNumber?: string | null; status: string; assignedTo?: AppUser | null; certificationDeadline?: string | null; heirs: InheritanceHeir[]; events: InheritanceEvent[]; updatedAt?: number | null; }
export interface InheritanceHeir { id: string; displayName: string; phone?: string | null; email?: string | null; contactStatus?: string | null; }
export interface InheritanceEvent { id: string; type: string; description: string; createdAt: number; }
export interface SalesTask { owner: Owner; markedParcelCount: number; openDealCount: number; nextReminder?: number | null; }
export interface IntegrationJob { key: string; label: string; configured: boolean; lastRun?: { id: number; status: string; finishedAt?: number | null; error?: string | null } | null; }
