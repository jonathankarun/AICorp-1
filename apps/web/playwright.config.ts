import { defineConfig } from "@playwright/test";
const baseURL = `http://127.0.0.1:${process.env.AICORP_PORT || "8000"}`;
export default defineConfig({
  testDir: "tests",
  workers: 1,
  use: {
    baseURL,
    headless: true,
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
  webServer: {
    command: `"${process.env.AICORP_PYTHON || "../../.venv/bin/python"}" ../../scripts/serve_week2.py`,
    url: `${baseURL}/api/v1/health`,
    reuseExistingServer: false,
    timeout: 30000,
  },
});
