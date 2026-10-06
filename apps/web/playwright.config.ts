import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "tests",
  workers: 1,
  use: {
    baseURL: "http://127.0.0.1:8000",
    headless: true,
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
  webServer: {
    command: `"${process.env.AICORP_PYTHON || "../../.venv/bin/python"}" ../../scripts/serve_week2.py`,
    url: "http://127.0.0.1:8000/api/v1/health",
    reuseExistingServer: false,
    timeout: 30000,
  },
});
