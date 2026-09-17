import { defineConfig } from '@playwright/test';

const BACKEND = 'http://127.0.0.1:10780';
const FRONTEND = 'http://127.0.0.1:10781';

export default defineConfig({
  testDir: './e2e',
  timeout: 60000,
  retries: 1,
  fullyParallel: true,
  use: {
    baseURL: FRONTEND,
    headless: true,
    screenshot: 'only-on-failure',
    trace: 'on-first-retry',
  },
  webServer: [
    {
      command: 'uv run uvicorn browser_mcp.app:app --host 127.0.0.1 --port 10780 --log-level warning',
      url: `${BACKEND}/health`,
      cwd: '../',
      reuseExistingServer: false,
      timeout: 30000,
    },
    {
      command: 'npm run dev -- --port 10781 --strictPort',
      url: FRONTEND,
      cwd: '.',
      reuseExistingServer: false,
      timeout: 60000,
    },
  ],
});
