import type { Page, Route } from "@playwright/test";

type SeedRole = "admin" | "viewer";

const owner = {
  id: "79601:001:9999",
  name: "Metsaomanik Mari",
  version: 1,
  status: "IN_PROGRESS",
  phone: "+372 5550 0000",
  email: "mari@example.test",
  address: "Metsatee 1",
  cadastres: [
    { id: "79601:001:9999", name: "Kuusiku", area: 12.4, marked: true },
  ],
};

const adminClaims = {
  userId: "qa-admin",
  userName: "QA Admin",
  privileges: [
    "ADMIN",
    "OWNER_PROFILE",
    "ASSIGNED_OWNERS",
    "EVALUATION",
    "PHONES",
  ],
  roles: ["ORG_ADMIN"],
  organizationId: "qa-org",
  exp: 4_102_444_800,
};
const viewerClaims = {
  userId: "qa-viewer",
  userName: "QA Viewer",
  privileges: [],
  roles: ["VIEWER"],
  organizationId: "qa-org",
  exp: 4_102_444_800,
};

function token(claims: object): string {
  const encode = (value: object) =>
    Buffer.from(JSON.stringify(value)).toString("base64url");
  return `${encode({ alg: "none", typ: "JWT" })}.${encode(claims)}.deterministic-signature`;
}

export const seededTokens = {
  admin: token(adminClaims),
  viewer: token(viewerClaims),
  preAuth: token({ userId: "qa-admin", purpose: "pre-auth" }),
};

function json(route: Route, body: unknown, status = 200) {
  return route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify(body),
  });
}

export async function installSeededApi(page: Page) {
  const deals = [
    {
      id: "deal-0001",
      version: 1,
      owner,
      saleSubject: "FOREST",
      stage: "EVALUATION",
      parcels: owner.cadastres,
      offers: [],
    },
  ];
  const inheritanceCases = [
    {
      id: "case-0001",
      version: 1,
      owner,
      sourceNoticeNumber: "P-2026-1",
      status: "NEW",
      heirs: [],
    },
  ];

  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const { pathname } = new URL(request.url());
    const method = request.method();
    if (pathname === "/api/oidc/config")
      return json(route, { enabled: false, localLoginEnabled: true });
    if (pathname === "/api/password-login" && method === "POST")
      return json(route, { token: seededTokens.preAuth });
    if (pathname === "/api/services/totp" && method === "POST")
      return json(route, {
        actualToken: { token: seededTokens.admin },
        refreshToken: { token: seededTokens.admin },
      });
    if (pathname === `/api/services/owners/${owner.id}` && method === "GET")
      return json(route, owner);
    if (pathname === "/api/services/owner-statuses")
      return json(route, [
        {
          id: "IN_PROGRESS",
          durationDays: 60,
          colorHex: "c5edc8",
          protectedStatus: true,
        },
      ]);
    if (pathname === `/api/services/deals/owners/${owner.id}`)
      return json(route, deals);
    if (pathname === `/api/services/inheritance/owners/${owner.id}`)
      return json(route, inheritanceCases);
    if (pathname === `/api/services/ownership-transitions/owners/${owner.id}`)
      return json(route, []);
    if (
      pathname.includes("/services/deals/") &&
      pathname.endsWith("/evaluations") &&
      method === "POST"
    ) {
      deals[0] = { ...deals[0], version: 2, stage: "NEGOTIATION" };
      return json(route, deals[0]);
    }
    if (
      pathname.includes("/services/deals/") &&
      pathname.endsWith("/commercial/offers") &&
      method === "POST"
    )
      return json(
        route,
        { offer: { id: "offer-0001" }, state: { version: 3 } },
        201,
      );
    if (
      pathname.includes("/services/deals/") &&
      pathname.endsWith("/commercial/offers/send") &&
      method === "POST"
    ) {
      deals[0] = {
        ...deals[0],
        version: 4,
        stage: "WON",
        offers: [
          {
            id: "offer-0001",
            revision: 1,
            kind: "OFFER",
            status: "SENT",
            amount: 125000,
          },
        ],
      };
      return json(route, deals[0]);
    }
    if (
      pathname === "/api/services/contracts/generate-from-deal" &&
      method === "POST"
    )
      return json(route, { contractId: "contract-0001" }, 201);
    if (pathname.includes("/official-notices/check") && method === "POST")
      return json(route, { notices: [] });
    if (
      pathname === `/api/services/inheritance/owners/${owner.id}` &&
      method === "POST"
    )
      return json(route, inheritanceCases[0], 201);
    if (
      pathname.includes("/inheritance/cases/") &&
      pathname.endsWith("/status") &&
      method === "PATCH"
    ) {
      inheritanceCases[0] = { ...inheritanceCases[0], status: "IN_PROGRESS" };
      return json(route, inheritanceCases[0]);
    }
    if (
      pathname === "/api/services/owners/imports/inspect" &&
      method === "POST"
    )
      return json(route, { suggestedMapping: { id: "id", name: "name" } });
    if (
      pathname === "/api/services/owners/imports/preview" &&
      method === "POST"
    )
      return json(route, {
        sha256: "deterministic-owner-import",
        readyCount: 1,
        rejectedCount: 0,
        rows: [
          {
            rowNumber: 2,
            id: "owner-2",
            name: "Seed owner",
            status: "READY",
            reason: "",
          },
        ],
      });
    if (pathname === "/api/services/owners/imports/commit" && method === "POST")
      return json(route, { created: 1, updated: 0 }, 201);
    if (pathname === "/api/services/map/cadastres")
      return json(route, {
        type: "FeatureCollection",
        features: [
          {
            type: "Feature",
            id: "qa-cadastre",
            properties: {
              id: owner.cadastres[0].id,
              cadastreId: owner.cadastres[0].id,
              name: owner.cadastres[0].name,
            },
            geometry: {
              type: "Polygon",
              coordinates: [
                [
                  [25.58, 58.68],
                  [25.62, 58.68],
                  [25.62, 58.72],
                  [25.58, 58.72],
                  [25.58, 58.68],
                ],
              ],
            },
          },
        ],
      });
    if (
      pathname === `/api/services/cadastres/${owner.cadastres[0].id}/workspace`
    )
      return json(route, {
        cadastre: {
          id: owner.cadastres[0].id,
          name: owner.cadastres[0].name,
          area: 12.4,
          county: "Jõgeva",
          address: "Metsatee 1",
        },
        owners: [
          {
            id: owner.id,
            name: owner.name,
            phone: owner.phone,
            email: owner.email,
            customerRelationship: {
              isCustomer: true,
              ownerStatus: "IN_PROGRESS",
              activeDealCount: 1,
              wonDealCount: 0,
            },
          },
        ],
        activities: [],
        notifications: [],
        registryFeatures: [],
        customerSummary: { customerOwnerCount: 1 },
      });
    if (pathname.includes("/services/map/"))
      return json(route, { type: "FeatureCollection", features: [] });
    if (pathname === "/api/services/status")
      return json(route, { status: "OK", service: "forestiq-django" });
    return json(route, []);
  });
}

export async function authenticateSeededUser(
  page: Page,
  role: SeedRole = "admin",
) {
  await page.addInitScript(
    ({ selectedRole, accessToken }) => {
      localStorage.clear();
      localStorage.setItem("forestiq_access_token", accessToken[selectedRole]);
    },
    { selectedRole: role, accessToken: seededTokens },
  );
}
