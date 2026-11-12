import { test, expect } from "@playwright/test";

test("smoke: application loads with header and dark mode toggle", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveTitle(/Cart Detective/);
  await expect(page.locator("header")).toBeVisible();
  await expect(page.getByRole("link", { name: "Cart Detective" })).toBeVisible();
  await expect(page.getByLabel("Toggle theme")).toBeVisible();
});
