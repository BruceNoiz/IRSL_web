import { defineConfig } from '@playwright/test';

const base = `/${(process.env.BASE_PATH || '/IRSL_web/').split('/').filter(Boolean).join('/')}`;
const basePath = base === '/' ? base : `${base}/`;

export default defineConfig({
  testDir: './tests/browser',
  outputDir: '.agent/logs/website/browser-results',
  reporter: 'list',
  use: { baseURL: `http://127.0.0.1:4322${basePath}`, browserName: 'chromium' },
  webServer: [
    {
      command: 'python3 tests/serve_static.py',
      url: `http://127.0.0.1:4322${basePath}`,
      env: { BASE_PATH: basePath },
      reuseExistingServer: false,
    },
    {
      command: 'npm run dev -- --ignore-lock --host 127.0.0.1 --port 4324',
      url: `http://127.0.0.1:4324${basePath}`,
      env: { BASE_PATH: basePath, ASTRO_TELEMETRY_DISABLED: '1', ASTRO_DEV_BACKGROUND: '0' },
      reuseExistingServer: false,
    },
    {
      command: 'npm run preview -- --ignore-lock --host 127.0.0.1 --port 4325',
      url: `http://127.0.0.1:4325${basePath}`,
      env: { BASE_PATH: basePath, ASTRO_TELEMETRY_DISABLED: '1', ASTRO_PREVIEW_BACKGROUND: '0' },
      reuseExistingServer: false,
    },
  ],
});
