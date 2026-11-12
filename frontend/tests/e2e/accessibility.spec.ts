import { test, expect } from "@playwright/test";
import axe from "axe-core";

test.describe("Accessibility WCAG AA checks", () => {
  const routes = [
    { name: "Search (home)", path: "/" },
    { name: "History", path: "/history" },
    { name: "Wishlist", path: "/wishlist" },
    { name: "Bought", path: "/bought" },
    { name: "Settings", path: "/settings" },
  ];

  for (const route of routes) {
    test(`accessibility: ${route.name} page passes axe WCAG AA audit`, async ({ page }) => {
      await page.goto(route.path);
      await page.waitForLoadState("domcontentloaded");

      // Inject axe-core source
      await page.evaluate(axe.source);

      // Run axe on document
      const results = await page.evaluate(async () => {
        // @ts-expect-error window.axe injected above
        return await window.axe.run(document, {
          runOnly: {
            type: "tag",
            values: ["wcag2a", "wcag2aa"],
          },
        });
      });

      const violations = results.violations.map((v: { id: string; description: string; nodes: unknown[] }) => ({
        id: v.id,
        description: v.description,
        nodes: v.nodes.length,
      }));

      expect(violations).toEqual([]);
    });
  }
});
