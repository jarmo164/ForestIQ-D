import { expect, test } from "@playwright/test";

import { authenticateSeededUser, installSeededApi } from "./seed";

const ownerId = "79601:001:9999";

test.beforeEach(async ({ page }) => {
  await authenticateSeededUser(page, "admin");
  await installSeededApi(page);
});

test("Owner 360 API failure is visible with correlation reference and retry", async ({ page }) => {
  await page.route(`**/api/services/owners/${ownerId}/360/summary`, async (route) => {
    await route.fulfill({
      status: 503,
      headers: { "content-type": "application/json", "X-Correlation-ID": "qa-owner-360-error" },
      body: JSON.stringify({ detail: "Owner 360 unavailable" }),
    });
  });

  await page.goto(`/owners/${ownerId}`);

  await expect(page.getByRole("alert").filter({ hasText: "Owner 360 unavailable" })).toContainText("qa-owner-360-error");
  await expect(page.getByRole("button", { name: "Proovi uuesti" }).first()).toBeVisible();
});

test("P1 operations failure is not rendered as an empty deal list", async ({ page }) => {
  await page.route("**/api/services/deals/workbench**", async (route) => {
    await route.fulfill({
      status: 503,
      headers: { "content-type": "application/json", "X-Correlation-ID": "qa-p1-error" },
      body: JSON.stringify({ detail: "Workbench unavailable" }),
    });
  });

  await page.goto("/operations");

  const alert = page.getByRole("alert").filter({ hasText: "Workbench unavailable" });
  await expect(alert).toContainText("qa-p1-error");
  await expect(page.getByText("Filtritele vastavaid aktiivseid tehinguid ei ole.")).toHaveCount(0);
  await expect(alert.getByRole("button", { name: "Proovi uuesti" })).toBeVisible();
});

test("destructive profile deletion can be cancelled and cannot double-submit", async ({ page }) => {
  let deleteCalls = 0;
  await page.route("**/api/services/company-profiles/company-0001", async (route) => {
    if (route.request().method() !== "DELETE") return route.fallback();
    deleteCalls += 1;
    await new Promise((resolve) => setTimeout(resolve, 150));
    await route.fulfill({ status: 204, body: "" });
  });

  await page.goto("/contracts");
  await page.getByRole("button", { name: "Mallid ja ettevõtted" }).click();

  await page.getByRole("button", { name: "Kustuta" }).click();
  const firstDialog = page.getByRole("dialog", { name: "Kustuta ettevõtteprofiil?" });
  await expect(firstDialog).toBeVisible();
  await firstDialog.getByRole("button", { name: "Tühista" }).click();
  await expect(firstDialog).not.toBeVisible();
  expect(deleteCalls).toBe(0);

  await page.getByRole("button", { name: "Kustuta" }).click();
  const dialog = page.getByRole("dialog", { name: "Kustuta ettevõtteprofiil?" });
  const confirm = dialog.getByRole("button", { name: "Kustuta" });
  await confirm.click();
  await expect(dialog.getByRole("button", { name: "Töötlen…" })).toBeDisabled();
  expect(deleteCalls).toBe(1);
  await page.waitForTimeout(200);
  expect(deleteCalls).toBe(1);
});
