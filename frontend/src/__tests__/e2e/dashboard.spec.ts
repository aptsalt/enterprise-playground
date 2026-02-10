import { test, expect } from "@playwright/test";

test.describe("Dashboard", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
  });

  test("page loads with correct title", async ({ page }) => {
    await expect(page).toHaveTitle(/Enterprise Playground/);
  });

  test("all 7 tab buttons are visible", async ({ page }) => {
    const tabs = ["Generate", "Gallery", "Pipeline", "Data & RAG", "ML Metrics", "Observatory", "Agent"];
    for (const tab of tabs) {
      await expect(page.getByRole("button", { name: tab })).toBeVisible();
    }
  });

  test("default tab is Generate with prompt input visible", async ({ page }) => {
    await expect(page.getByTestId("prompt-input")).toBeVisible();
  });

  test("tab switching works - Gallery", async ({ page }) => {
    await page.getByRole("button", { name: "Gallery" }).click();
    await expect(page.getByTestId("gallery-search")).toBeVisible();
    await expect(page.getByTestId("prompt-input")).not.toBeVisible();
  });

  test("tab switching works - Pipeline", async ({ page }) => {
    await page.getByRole("button", { name: "Pipeline" }).click();
    await expect(page.getByText("ML Pipeline")).toBeVisible();
  });

  test("VRAM bar renders in nav", async ({ page }) => {
    await expect(page.locator("header").getByText("%")).toBeVisible();
  });

  test("model status dots render", async ({ page }) => {
    await expect(page.getByText("14B")).toBeVisible();
    await expect(page.getByText("3B")).toBeVisible();
  });
});
