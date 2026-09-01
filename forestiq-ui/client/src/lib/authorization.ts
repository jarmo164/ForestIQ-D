import type { AppUser, OrganizationRole, Privilege } from "@/lib/types";

export type AccessRequirement = {
  anyPrivileges?: readonly Privilege[];
  anyRoles?: readonly OrganizationRole[];
};

export type NavigationItem = {
  label: string;
  href: string;
  requirement?: AccessRequirement;
};

const withPrivilege = (...anyPrivileges: Privilege[]): AccessRequirement => ({ anyPrivileges });

export const routeAccess: Record<string, AccessRequirement | undefined> = {
  "/owners": withPrivilege("ADMIN", "OWNER_PROFILE", "ASSIGNED_OWNERS"),
  "/owners/import": withPrivilege("ADMIN", "OWNER_PROFILE", "ASSIGNED_OWNERS"),
  "/map": withPrivilege("ADMIN", "OWNER_PROFILE", "ASSIGNED_OWNERS", "EVALUATION"),
  "/deals": withPrivilege("ADMIN", "OWNER_PROFILE", "EVALUATION"),
  "/inheritance": withPrivilege("ADMIN", "OWNER_PROFILE", "ASSIGNED_OWNERS"),
  "/sales": withPrivilege("ADMIN", "OWNER_PROFILE", "ASSIGNED_OWNERS"),
  "/integrations": withPrivilege("ADMIN"),
  "/management": { anyRoles: ["ORG_OWNER", "ORG_ADMIN", "CRM_MANAGER"] },
  "/workdesk/caller": withPrivilege("ADMIN", "ASSIGNED_OWNERS"),
  "/workdesk/evaluator": withPrivilege("ADMIN", "EVALUATION"),
  "/workdesk/admin": withPrivilege("ADMIN"),
  "/admin": withPrivilege("ADMIN"),
  "/contracts": withPrivilege("ADMIN"),
  "/phones": withPrivilege("ADMIN", "PHONES"),
};

export const navigationItems: readonly NavigationItem[] = [
  { label: "Töölaud", href: "/home" },
  { label: "Omanikud", href: "/owners", requirement: routeAccess["/owners"] },
  { label: "Müügijärjekord", href: "/sales", requirement: routeAccess["/sales"] },
  { label: "Tehingud", href: "/deals", requirement: routeAccess["/deals"] },
  { label: "Pärimine", href: "/inheritance", requirement: routeAccess["/inheritance"] },
  { label: "Kaart", href: "/map", requirement: routeAccess["/map"] },
  { label: "Hindamine", href: "/workdesk/evaluator", requirement: routeAccess["/workdesk/evaluator"] },
  { label: "Meeldetuletused", href: "/reminders" },
  { label: "Sõnumid", href: "/messages" },
  { label: "Lepingud", href: "/contracts", requirement: routeAccess["/contracts"] },
  { label: "Kontaktid", href: "/phones", requirement: routeAccess["/phones"] },
  { label: "Import", href: "/owners/import", requirement: routeAccess["/owners/import"] },
  { label: "Integratsioonid", href: "/integrations", requirement: routeAccess["/integrations"] },
  { label: "Juhtimine", href: "/management", requirement: routeAccess["/management"] },
  { label: "Haldus", href: "/admin", requirement: routeAccess["/admin"] },
];

export function hasAccess(user: AppUser | null, requirement?: AccessRequirement): boolean {
  if (!user) return false;
  if (!requirement) return true;
  const privilegeAllowed = !requirement.anyPrivileges?.length || requirement.anyPrivileges.some((code) => user.privileges.includes(code));
  const roleAllowed = !requirement.anyRoles?.length || requirement.anyRoles.some((role) => user.roles.includes(role));
  return privilegeAllowed && roleAllowed;
}

export function requirementForPath(pathname: string): AccessRequirement | undefined {
  const matchedPath = Object.keys(routeAccess)
    .filter((path) => pathname === path || pathname.startsWith(`${path}/`))
    .sort((left, right) => right.length - left.length)[0];
  return matchedPath ? routeAccess[matchedPath] : undefined;
}
