/** ForestIQ Landscape Desk design: quiet Nordic data tooling with crisp operational hierarchy. */
export type Privilege = "ADMIN" | "OWNER_PROFILE" | "ASSIGNED_OWNERS" | "PHONES" | "EVALUATION";
export interface AppUser { id: string; name: string; privileges: Privilege[]; }
export interface Owner { id: string; name: string; status?: string | null; statusSetAt?: number | null; assignee?: { id: string; name: string } | null; phone?: string | null; email?: string | null; address?: string | null; info?: string | null; type?: string | null; cadastres?: Cadastre[]; }
export interface Cadastre { id: string; name?: string | null; marked?: boolean; area?: number | null; forestArea?: number | null; type?: string | null; county?: string | null; municipality?: string | null; address?: string | null; labels?: string[]; }
export interface Reminder { id: string; text: string; dueTime: number; owner?: Owner | null; creator?: string; }
export interface Message { id: string; message: string; createdAt: number; sender?: { id: string; name: string } | null; recipient?: { id: string; name: string } | null; }
export interface OwnerStatus { id: string; colorHex: string; durationDays: number; protectedStatus: boolean; }
