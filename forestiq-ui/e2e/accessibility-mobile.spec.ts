import { expect, test } from "@playwright/test";

import { authenticateSeededUser, installSeededApi } from "./seed";

const ownerId = "79601:001:9999";

test.beforeEach(async ({ page }) => {
  await authenticateSeededUser(page, "admin");
  await installSeededApi(page);
});

test("mobile owner registry keeps contact, assignee, primary action and navigation visible", async ({ page }) => {
  await page.goto("/owners");

  const row = page.getByRole("link", { name: /Metsaomanik Mari/ });
  await expect(row).toBeVisible();
  await expect(row).toContainText("+372 5550 0000");
  await expect(row).toContainText("mari@example.test");
  await expect(row).toContainText("QA Admin");

  const navigation = page.getByRole("navigation");
  await expect(navigation).toBeVisible();
  await expect(page.getByRole("link", { name: /Omanikud/ })).toBeVisible();

  await row.press("Enter");
  await expect(page).toHaveURL(new RegExp(`/owners/${ownerId}$`));
});

test("P1 tabs support arrow, Home and End keyboard navigation", async ({ page }) => {
  await page.goto("/operations");

  const deals = page.getByRole("tab", { name: "Tehingu tervis" });
  const quality = page.getByRole("tab", { name: "Andmekvaliteet" });
  const contracts = page.getByRole("tab", { name: "Lepingukontroll" });

  await deals.focus();
  await page.keyboard.press("ArrowRight");
  await expect(quality).toBeFocused();
  await expect(quality).toHaveAttribute("aria-selected", "true");
  await expect(page.getByRole("tabpanel", { name: "Andmekvaliteet" })).toBeVisible();

  await page.keyboard.press("End");
  await expect(contracts).toBeFocused();
  await expect(contracts).toHaveAttribute("aria-selected", "true");

  await page.keyboard.press("Home");
  await expect(deals).toBeFocused();
  await expect(deals).toHaveAttribute("aria-selected", "true");
});

test("map search, cadastre dialog and workbasket are keyboard-operable", async ({ page }) => {
  await page.goto("/map");

  const search = page.getByLabel("Katastritunnus või aadress");
  await search.fill("796");
  await search.press("Enter");

  const result = page.getByRole("button", { name: /Kuusiku/ }).first();
  await expect(result).toBeVisible();
  await result.press("Enter");

  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible();
  const close = dialog.getByRole("button", { name: "Sulge detailaken" });
  await expect(close).toBeFocused();

  await page.keyboard.press("Tab");
  expect(await dialog.evaluate((node) => node.contains(document.activeElement))).toBe(true);

  await page.keyboard.press("Escape");
  await expect(dialog).not.toBeVisible();
  await expect(result).toBeFocused();

  await page.locator("#map-basket-name").fill("QA keyboard basket");
  await page.locator("#map-basket-purpose").fill("Accessibility test");
  const save = page.getByRole("button", { name: "Salvesta" });
  await save.focus();
  await save.press("Enter");
  await expect(page.getByText("QA keyboard basket salvestatud.")).toBeVisible();
});
