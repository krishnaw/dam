import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  timeout: 30000,
  retries: 1,
  workers: 1,
  use: {
    headless: true,
    baseURL: "http://localhost:3001",
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
  projects: [
    { name: "chromium", use: { browserName: "chromium" } },
  ],
  webServer: {
    command: "npm run dev -- --port 3001",
    cwd: "./frontend",
    port: 3001,
    reuseExistingServer: true,
    timeout: 30000,
  },
});
