import { expect, test } from "@playwright/test";

import { authenticateSeededUser, installSeededApi } from "./seed";

const ownerPath = "/owners/79601:001:9999";

test.beforeEach(async ({ page }) => {
  await installSeededApi(page);
});

test("login opens the deterministic development workspace", async ({
  page,
}) => {
  await page.goto("/");
  await page.locator("input").nth(0).fill("qa-admin");
  await page.locator("input").nth(1).fill("deterministic-password");
  await page.locator("input").nth(2).fill("000000");
  await page.getByRole("button", { name: "Ava arendustöölaud" }).click();

  await expect(page).toHaveURL(/\/home$/);
  await expect(page.getByText("Töölaud").first()).toBeVisible();
});

test("owner workflow completes evaluation, offer and template-based contract generation", async ({
  page,
}) => {
  await authenticateSeededUser(page);
  await page.goto(ownerPath);
  await expect(
    page.getByRole("heading", { name: "Metsaomanik Mari", level: 2 }),
  ).toBeVisible();

  await page.getByLabel("Hindamise pakkumishind").fill("125000");
  await page.getByRole("button", { name: "Kinnita hindamine" }).click();
  await page.getByLabel("Pakkumise summa").fill("125000");
  await page.getByRole("button", { name: "Saada pakkumine" }).click();
  await page.getByRole("link", { name: "Koosta leping" }).click();
  await expect(page.getByRole("heading", { name: "Lepingute tööala", level: 1 })).toBeVisible();
  await page.getByRole("button", { name: "Laadi tehing" }).click();
  await expect(page.getByText("Metsaomanik Mari").last()).toBeVisible();
  await expect(page.getByText("ForestIQ OÜ").last()).toBeVisible();
  await page.getByRole("button", { name: "Eelvaade" }).click();
  await expect(page.getByTitle("Lepingumalli eelvaade")).toBeVisible();
  await page.getByRole("button", { name: "Genereeri PDF" }).click();
  await expect(page.getByText("Leping contract-0001 loodi serveripoolse PDF-iga.")).toBeVisible();
});

test("owner workflow creates and starts an inheritance case", async ({
  page,
}) => {
  await authenticateSeededUser(page);
  await page.goto(ownerPath);
  await expect(
    page.getByRole("button", { name: "Kontrolli teadet" }),
  ).toBeVisible();

  await page.getByRole("button", { name: "Kontrolli teadet" }).click();
  await page.getByRole("button", { name: "Loo juhtum" }).click();
  await page.getByRole("button", { name: "Võta töösse" }).click();

  await expect(page.getByText("IN PROGRESS").first()).toBeVisible();
});

test("owner import inspects, previews and commits one seeded CSV row", async ({
  page,
}) => {
  await authenticateSeededUser(page);
  await page.goto("/owners/import");
  await page.locator('input[type="file"]').setInputFiles({
    name: "owners.csv",
    mimeType: "text/csv",
    buffer: Buffer.from("id,name\nowner-2,Seed owner\n"),
  });
  await page.getByRole("button", { name: "Kontrolli faili" }).click();

  await expect(page.getByText("1 valmis · 0 tagasi lükatud")).toBeVisible();
  await page.getByRole("button", { name: "Impordi 1 rida" }).click();
  await expect(page.getByText("EELVAADE")).not.toBeVisible();
});

test("viewer receives a visible 403 and cannot trigger integration data requests", async ({
  page,
}) => {
  const requestedUrls: string[] = [];
  page.on("request", (request) =>
    requestedUrls.push(new URL(request.url()).pathname),
  );
  await authenticateSeededUser(page, "viewer");
  await page.goto("/integrations");

  await expect(
    page.getByRole("heading", { name: "403 — puudub ligipääsuõigus" }),
  ).toBeVisible();
  expect(requestedUrls).not.toContain("/api/services/admin/integrations");
});

test("map workspace renders its interactive map and cadastre guidance", async ({
  page,
}) => {
  await authenticateSeededUser(page);
  await page.goto("/map");

  await expect(
    page.getByRole("heading", { name: "Metsa- ja katastrivaade" }),
  ).toBeVisible();
  await expect(
    page.getByLabel("Interaktiivne ForestIQ GeoDjango kaart"),
  ).toBeVisible();
  await expect(
    page.getByText("Suured katastri- ja registrikihid laetakse MVT-paanidena"),
  ).toBeVisible();
});

test("admin sees integration freshness, opens sync-run detail and triggers recovery", async ({
  page,
}) => {
  const recoveryRequests: string[] = [];
  page.on("request", (request) => {
    const pathname = new URL(request.url()).pathname;
    if (pathname === "/api/services/registry/freshness/recover")
      recoveryRequests.push(pathname);
  });
  await authenticateSeededUser(page);
  await page.goto("/integrations");

  await expect(
    page.getByRole("heading", {
      name: "Andmete värskus ja integratsioonide tervis",
    }),
  ).toBeVisible();
  await expect(page.getByLabel("cadastre tervis")).toContainText(
    "VAJAB TÄHELEPANU",
  );
  await expect(page.getByLabel("parimus tervis")).toContainText("TÖÖKORRAS");

  await page.getByRole("button", { name: "Ava jooksu detail" }).first().click();
  await expect(
    page.getByRole("dialog", { name: "cadastre_wfs" }),
  ).toContainText("Jooks #321");
  await expect(
    page.getByText("Metsaregistri lähteallikas vastas ajutise tõrkega."),
  ).toBeVisible();
  await page.getByRole("button", { name: "Sulge detail" }).click();

  await page.getByRole("button", { name: "Taasta aegunud" }).click();
  await expect.poll(() => recoveryRequests.length).toBe(1);
});
