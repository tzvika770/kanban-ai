import { expect, test, type Page } from "@playwright/test";

// These tests exercise the full integrated app (auth + backend persistence)
// served by FastAPI at the configured baseURL.

async function login(page: Page) {
  await page.goto("/login/");
  await page.getByLabel("Username").fill("user");
  await page.getByLabel("Password").fill("password");
  await page.getByRole("button", { name: "Sign In" }).click();
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
  // Let the initial board fetch settle so optimistic edits aren't overwritten.
  await page.waitForLoadState("networkidle");
}

test("logs in and shows the five-column board", async ({ page }) => {
  await login(page);
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(5);
});

test("adds a card and it persists across reload", async ({ page }) => {
  await login(page);
  const firstColumn = page.locator('[data-testid^="column-"]').first();
  const title = `Playwright card ${Date.now()}`;

  await firstColumn.getByRole("button", { name: /add a card/i }).click();
  await firstColumn.getByPlaceholder("Card title").fill(title);
  await firstColumn.getByPlaceholder("Details").fill("Added via e2e.");
  await firstColumn.getByRole("button", { name: /add card/i }).click();

  await expect(firstColumn.getByText(title)).toBeVisible();

  // Reload: the card is only still there if it was saved to the backend.
  await page.waitForLoadState("networkidle");
  await page.reload();
  await page.waitForLoadState("networkidle");
  await expect(page.getByText(title)).toBeVisible();
});

test("moves a card to the next column with the arrow button", async ({ page }) => {
  await login(page);
  const firstColumn = page.locator('[data-testid^="column-"]').first();
  const firstCard = firstColumn.locator('[data-testid^="card-"]').first();
  await expect(firstCard).toBeVisible();
  const title = (await firstCard.locator("h4").innerText()).trim();

  // Move an existing (persisted) card so it has a real backend id.
  await firstCard.getByRole("button", { name: /to next column/i }).click();

  const secondColumn = page.locator('[data-testid^="column-"]').nth(1);
  await expect(secondColumn.getByText(title, { exact: true })).toBeVisible();
});
