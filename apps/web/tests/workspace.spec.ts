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
  await expect(page.getByText("ready", { exact: true })).toBeVisible();
  await page.getByRole("checkbox").check();
  await page.getByLabel("Request type").selectOption("RFP");
  await page.getByRole("button", { name: "Save assignment" }).click();
  await expect(page.getByRole("status")).toContainText("Assignment saved");
  await page.reload();
  await page.getByRole("button", { name: "Connect", exact: true }).click();
  await expect(page.getByLabel("Problem", { exact: true })).toHaveValue(
    "Improve permit intake",
  );
  await expect(page.getByRole("checkbox")).toBeChecked();
  await expect(page.getByLabel("Request type")).toHaveValue("RFP");
  await page.getByLabel("Search query").fill("timeline");
  await page.getByRole("button", { name: "Search evidence" }).click();
  await expect(page.locator("article")).toContainText("six weeks");
  await expect(page.locator("article h3")).toContainText("page 1");
  await page.getByRole("button", { name: "Preview mock report" }).click();
  const report = page.getByRole("region", { name: "mock report" });
  await expect(report).toContainText("Structured mock report");
  await expect(report).toContainText("Mock evidence preview");
  await page.screenshot({ path: "../../evidence/local/integrated-report.png", fullPage: true });
  await report.getByRole("button", { name: /cite-/ }).first().click();
  await expect(page.getByLabel("source details")).toContainText("Document version:");
  await expect(page.getByLabel("source details")).toContainText("page ");
  await page.getByLabel("Problem", { exact: true }).fill("Improve permit intake with review");
  await expect(page.getByRole("button", { name: "Preview mock report" })).toBeDisabled();
  await expect(report).toHaveCount(0);
  await page.getByLabel("Problem", { exact: true }).fill("Improve permit intake");
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
