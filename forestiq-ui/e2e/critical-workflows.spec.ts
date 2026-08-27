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

test("owner workflow completes evaluation, offer and contract draft", async ({
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
  await page.getByRole("button", { name: "Koosta lepingu draft" }).click();

  await expect(
    page.getByText("Lepingu contract-0001 draft on loodud."),
  ).toBeVisible();
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
  await page
    .locator('input[type="file"]')
    .setInputFiles({
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
  await expect(page.getByText("Suured katastri- ja registrikihid laetakse MVT-paanidena")).toBeVisible();
});
