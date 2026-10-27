// this file checks the workspace in a real browser
// it makes sure saved inputs survive reloads and errors stay visible
import { test, expect } from "@playwright/test";
import path from "node:path";
const token = process.env.AICORP_DEMO_TOKEN!;
test("real upload, saved selection, reload, source search, and failure preserves form", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByLabel("Local demo token").fill(token);
  await page.getByRole("button", { name: "Connect", exact: true }).click();
  await page
    .getByLabel("Problem", { exact: true })
    .fill("Improve permit intake");
  await page
    .getByLabel("Intended result")
    .fill("A preliminary improvement plan");
  await page
    .getByLabel("PDF file")
    .setInputFiles(path.resolve("../../tests/fixtures/week2/engagement.pdf"));
  await page.getByRole("button", { name: "Upload PDF" }).click();
  await expect(page.getByText("ready", { exact: true }).first()).toBeVisible();
  await page.getByRole("checkbox").last().check();
  await page.getByRole("button", { name: "Save assignment" }).click();
  await expect(page.getByRole("status")).toContainText("Assignment saved");
  await page.reload();
  await page.getByRole("button", { name: "Connect", exact: true }).click();
  await expect(page.getByLabel("Problem", { exact: true })).toHaveValue(
    "Improve permit intake",
  );
  await expect(page.getByRole("checkbox").last()).toBeChecked();
  await page.getByLabel("Search query").fill("timeline");
  await page.getByRole("button", { name: "Search evidence" }).click();
  await expect(page.locator("article")).toContainText("six weeks");
  await expect(page.locator("article h3")).toContainText("page 1");
  await page
    .getByLabel("PDF file")
    .setInputFiles({
      name: "broken.pdf",
      mimeType: "application/pdf",
      buffer: Buffer.from("%PDF-1.4\nbroken"),
    });
  await page.getByRole("button", { name: "Upload PDF" }).click();
  await expect(page.getByText("failed", { exact: true })).toBeVisible();
  await expect(
    page.getByText("Choose a readable, uncorrupted PDF."),
  ).toBeVisible();
  await expect(page.getByLabel("Problem", { exact: true })).toHaveValue(
    "Improve permit intake",
  );
  await page.getByLabel("Search query").fill("quasar spectroscopy");
  await page.getByRole("button", { name: "Search evidence" }).click();
  await expect(page.getByText("No eligible evidence found.")).toBeVisible();
  await page.screenshot({
    path: "../../evidence/local/week2-browser.png",
    fullPage: true,
  });
});
test("API outage is visible and form remains intact", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("Local demo token").fill(token);
  await page.getByRole("button", { name: "Connect", exact: true }).click();
  await page.getByLabel("Problem", { exact: true }).fill("Keep this text");
  await page.getByLabel("Intended result").fill("Keep this result");
  await page.route("**/api/v1/assignments", (route) =>
    route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({ error: { code: "database_unavailable" } }),
    }),
  );
  await page.getByRole("button", { name: "Save assignment" }).click();
  await expect(page.getByRole("alert")).toContainText("Database unavailable");
  await expect(page.getByLabel("Problem", { exact: true })).toHaveValue(
    "Keep this text",
  );
});

test('data demo shows spending, audited correction, and comparable work', async ({ page }) => {
  await page.goto('/');
  await page.getByLabel('Local demo token').fill(token);
  await page.getByRole('button', { name: 'Connect', exact: true }).click();
  await page.getByRole('button', { name: 'Load spending' }).click();
  await expect(page.getByText('Consulting: $280.00', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Classify the unresolved $50 as consulting' }).click();
  await expect(page.getByText('Consulting: $330.00', { exact: true })).toBeVisible();
  await expect(page.getByText('unresolved → consulting:', { exact: false })).toBeVisible();
  await page.getByRole('button', { name: 'Find past work' }).click();
  await expect(page.getByText('specialty: process improvement', { exact: false })).toBeVisible();
  await page.getByLabel('Search query').fill('timeline');
  await page.getByRole('button', { name: 'Search evidence' }).click();
  await page.getByRole('button', { name: 'Open original PDF' }).first().click();
  await expect(page.getByTitle('Original source PDF').first()).toBeVisible();
  await page.screenshot({ path: '../../evidence/local/data-demo.png', fullPage: true });
  await page.reload();
  await page.getByRole('button', { name: 'Connect', exact: true }).click();
  await page.getByRole('button', { name: 'Load spending' }).click();
  await expect(page.getByText('Consulting: $330.00', { exact: true })).toBeVisible();
});
