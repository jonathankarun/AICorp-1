// this file checks the workspace in a real browser
// it makes sure saved inputs survive reloads and errors stay visible
import { test, expect } from "@playwright/test";
import path from "node:path";
import { readFile } from "node:fs/promises";
const token = process.env.AICORP_DEMO_TOKEN!;
test("real upload, saved selection, reload, source search, and failure preserves form", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByLabel("Local demo token").fill(token);
  await page.getByRole("button", { name: "Connect", exact: true }).click();
  await expect(page.getByRole("heading", { name: "From source documents to traceable evidence" })).toBeVisible();
  await expect(page.locator(".process-steps")).toContainText("Save an assignment to continue");
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
  await expect(page.locator(".process-steps")).toContainText("1 selected · Assignment saved");
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
  await expect(page.locator(".process-steps")).toContainText("passages from the last search");
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

test('guided demo runs without uploads, supports stepping and replay, and shows failures', async ({ page }) => {
  await page.goto('/');
  await page.getByLabel('Local demo token').fill(token);
  await page.getByRole('button', { name: 'Connect', exact: true }).click();
  await expect(page.getByText('Presenter notes:', { exact: false })).toHaveCount(0);
  await page.getByRole('button', { name: 'Run demo', exact: true }).click();
  const demo = page.locator('.guided-demo');
  await expect(demo).toContainText('Processing status: ready');
  await expect(demo).toContainText('six weeks');
  await page.getByRole('button', { name: 'Next', exact: true }).click();
  await expect(demo).toContainText('Improve permit intake');
  await page.getByRole('button', { name: 'Next', exact: true }).click();
  await expect(demo).toContainText('Query: timeline');
  await page.getByRole('button', { name: 'Next', exact: true }).click();
  await expect(page.getByTitle('Guided demo original PDF')).toBeVisible();
  await page.getByRole('button', { name: 'Next', exact: true }).click();
  await expect(demo).toContainText('Consulting: $280.00');
  await page.getByRole('button', { name: 'Next', exact: true }).click();
  await expect(demo).toContainText('Consulting: $280.00 → $330.00');
  await expect(demo).toContainText('not a human review');
  await page.getByRole('button', { name: 'Run demo again' }).click();
  await expect(demo).toContainText('Processing status: ready');
  await page.clock.install();
  await page.clock.fastForward(30000);
  await expect(demo.getByRole('heading', { name: '1. Ingest the PDF', exact: true })).toBeVisible();
  await expect(demo).toContainText('What happens:');
  await expect(demo).toContainText('Tools & methods:');
  await page.getByRole('button', { name: 'Next', exact: true }).click();
  await expect(demo).toContainText('Assignment ID:');
  await page.getByRole('button', { name: 'Previous', exact: true }).click();
  await expect(demo).toContainText('Processing status: ready');
  await page.screenshot({ path: '../../evidence/local/guided-demo.png', fullPage: true });
  await page.route('**/api/v1/demo/run', route => route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ error: { code: 'database_unavailable' } }) }));
  await page.getByRole('button', { name: 'Run demo again' }).click();
  await expect(demo.getByRole('alert')).toContainText('Database unavailable');
  await expect(page.getByRole('button', { name: 'Run demo', exact: true })).toBeEnabled();
});


test('validation tab runs real checks, preserves results across tabs, and downloads its report', async ({ page }) => {
  await page.goto('/');
  await page.getByLabel('Local demo token').fill(token);
  await page.getByRole('button', { name: 'Connect', exact: true }).click();
  await page.getByRole('tab', { name: 'Validation', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Data subsystem demo', exact: true })).toBeHidden();
  await page.getByRole('button', { name: 'Run validation', exact: true }).click();
  const panel = page.getByRole('tabpanel', { name: 'Validation', exact: true });
  await expect(panel.getByRole('status')).toHaveText('PASS — 15/15 checks passed');
  await expect(panel).toContainText('403 review_permission_required');
  await expect(panel).toContainText('Original PDF integrity (SHA-256)');
  const downloadPromise = page.waitForEvent('download');
  await page.getByRole('link', { name: 'Download report' }).click();
  const download = await downloadPromise;
  const report = JSON.parse(await readFile((await download.path())!, 'utf8'));
  expect(report.status).toBe('PASS');
  expect(report.checks).toHaveLength(15);
  expect(download.suggestedFilename()).toContain(report.run_id);
  await page.getByRole('tab', { name: 'Validation', exact: true }).focus();
  await page.keyboard.press('ArrowLeft');
  await expect(page.getByRole('tab', { name: 'Demo', exact: true })).toBeFocused();
  await expect(page.getByRole('heading', { name: 'Data subsystem demo', exact: true })).toBeVisible();
  await page.getByRole('tab', { name: 'Validation', exact: true }).click();
  await expect(panel.getByRole('status')).toHaveText('PASS — 15/15 checks passed');
  await page.screenshot({ path: '../../evidence/local/validation.png', fullPage: true });
  await page.route('**/api/v1/demo/validate', route => route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ error: { code: 'database_unavailable' } }) }));
  await page.getByRole('button', { name: 'Run validation', exact: true }).click();
  await expect(panel.getByRole('alert')).toContainText('Database unavailable');
  await expect(panel.getByRole('status')).toHaveCount(0);
  await expect(page.getByRole('link', { name: 'Download report' })).toHaveCount(0);
});

test('validation tab displays a failed check without claiming success', async ({ page }) => {
  await page.goto('/');
  await page.getByLabel('Local demo token').fill(token);
  await page.getByRole('button', { name: 'Connect', exact: true }).click();
  await page.getByRole('tab', { name: 'Validation', exact: true }).click();
  await page.route('**/api/v1/demo/validate', route => route.fulfill({ json: {
    run_id: 'browser-failure-display-test', status: 'FAIL', passed: 0, total: 1,
    completed_at: '2026-11-03T12:00:00Z', duration_ms: 10, scope: 'Failure-display test',
    checks: [{ name: 'Initial spending', status: 'FAIL', expected: '280.00', actual: '999.00' }],
  } }));
  await page.getByRole('button', { name: 'Run validation', exact: true }).click();
  const panel = page.getByRole('tabpanel', { name: 'Validation', exact: true });
  await expect(panel.getByRole('status')).toHaveText('FAIL — 0/1 checks passed');
  await expect(panel).toContainText('999.00');
  await expect(panel).toContainText('280.00');
});
