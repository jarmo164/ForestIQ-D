import { describe, expect, it } from "vitest";

import { hasAccess, navigationItems, requirementForPath } from "./authorization";
import type { AppUser } from "./types";

const admin: AppUser = { id: "admin", name: "Administrator", privileges: ["ADMIN"], roles: ["ORG_ADMIN"], organizationId: "org-1" };
const caller: AppUser = { id: "caller", name: "Helistaja", privileges: ["ASSIGNED_OWNERS"], roles: ["CALLER"], organizationId: "org-1" };
const viewer: AppUser = { id: "viewer", name: "Vaataja", privileges: [], roles: ["VIEWER"], organizationId: "org-1" };

describe("route authorization", () => {
  it("blocks forbidden routes before their workspace can mount", () => {
    expect(hasAccess(viewer, requirementForPath("/integrations"))).toBe(false);
    expect(hasAccess(caller, requirementForPath("/workdesk/evaluator"))).toBe(false);
    expect(hasAccess(caller, requirementForPath("/owners/79601:001:9999"))).toBe(true);
    expect(hasAccess(null, requirementForPath("/owners"))).toBe(false);
    expect(hasAccess(caller, requirementForPath("/inheritance/case-123"))).toBe(true);
    expect(hasAccess(viewer, requirementForPath("/inheritance/case-123"))).toBe(false);
    expect(hasAccess(admin, requirementForPath("/management"))).toBe(true);
    expect(hasAccess(caller, requirementForPath("/management"))).toBe(false);
  });

  it("exposes navigation entries only to roles with the required privileges", () => {
    const callerLinks = navigationItems.filter((item) => hasAccess(caller, item.requirement)).map((item) => item.href);
    const adminLinks = navigationItems.filter((item) => hasAccess(admin, item.requirement)).map((item) => item.href);

    expect(callerLinks).toContain("/owners");
    expect(callerLinks).not.toContain("/workdesk/evaluator");
    expect(callerLinks).not.toContain("/integrations");
    expect(callerLinks).not.toContain("/admin");
    expect(adminLinks).toContain("/integrations");
    expect(adminLinks).toContain("/admin");
    expect(adminLinks).toContain("/management");
    expect(callerLinks).not.toContain("/management");
  });

  it("does not treat an unrelated route as privileged", () => {
    expect(requirementForPath("/reminders")).toBeUndefined();
    expect(hasAccess(viewer, requirementForPath("/reminders"))).toBe(true);
  });
});
